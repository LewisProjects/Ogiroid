use std::error::Error as err;
use std::io::Cursor;
use std::time::Duration;

use crate::image_utils::level_embed;
use crate::state::{ids_to_bytes, DBFailure};
use crate::{Data, Db};
// use byteorder::{ByteOrder, LittleEndian};
use crate::format_embed;
use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use bytecheck::CheckBytes;
use poise::serenity_prelude::routing::RouteInfo;
use poise::serenity_prelude::{
    ButtonStyle, CacheHttp, Context as DefContext, CreateButton, CreateComponents, CreateEmbed,
    PartialGuild, User,
};
use poise::serenity_prelude::{Message, MessageType};
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::DB;
use rusttype::Font;
use tokio::time::Instant;

use image::{ImageOutputFormat, Rgb, RgbImage, Rgba, RgbaImage};
use imageproc::drawing::{
    draw_cross_mut, draw_filled_circle_mut, draw_filled_rect_mut, draw_hollow_circle_mut,
    draw_hollow_rect_mut, draw_line_segment_mut, draw_text_mut,
};
use imageproc::rect::Rect;

#[derive(Archive, Deserialize, Serialize, Debug, PartialEq)]
#[archive_attr(derive(CheckBytes, Debug))]
pub struct Level {
    pub xp: f32,
    pub boost_factor: f32,
}

impl Default for Level {
    fn default() -> Self {
        Level {
            xp: 0.0,
            boost_factor: 1.0,
        }
    }
}

impl Level {
    pub fn new(xp: f32, boost_factor: Option<f32>) -> Self {
        Level {
            xp,
            boost_factor: boost_factor.unwrap_or(1.0),
        }
    }

    pub fn incrase_xp(&mut self, msg_len: usize) {
        self.xp += {
            if msg_len < 50 {
                2.0
            } else {
                4.0
            }
        } * self.boost_factor
    }

    pub fn get_level(&self) -> (u64, u32) {
        let xp = self.xp as u64;
        ((xp / 1000), (xp % 1000) as u32)
    }
    pub fn xp_for_next_level(_xp: u32) -> u32 {
        1000
    }
}

pub async fn handle_new_message<'a>(
    ctx: &'a DefContext,
    // f_ctx: FrameworkContext<'a, Data, Box<dyn err + Send + Sync>>,
    data: &Data,
    message: &Message,
) -> Result<(), DBFailure> {
    if message.guild_id.is_none()
        || message.author.bot
        || message.content.len() < 5
        || ![
            MessageType::Regular,
            MessageType::ThreadStarterMessage,
            MessageType::InlineReply,
        ]
        .contains(&message.kind)
    {
        return Ok(());
    }
    let id = *message.author.id.as_u64();
    let cooldown = Duration::new(2, 0);
    if let Some(last_message) = data.cooldown.get_cf(&id, &data.level_cf) {
        let duration_since = last_message.as_ref().elapsed();
        if duration_since <= cooldown {
            return Ok(());
        }
    };
    data.cooldown
        .insert_with_ttl(id, Instant::now(), 1, cooldown)
        .await;
    let id = ids_to_bytes(
        *message.guild_id.unwrap().as_u64(),
        *message.author.id.as_u64(),
    );
    let Some(mut level) = data.db.get_cf(&id, &data.level_cf) else {
        let mut level = Level::new(0.0, None);
        level.incrase_xp(message.content.len());
        data.db.put_cf(&id, level, &data.level_cf)?;
        return Ok(())
    };
    level.incrase_xp(message.content.len());
    data.db.put_cf(&id, level, &data.level_cf)?;
    Ok(())
}

/// Displays your or another user's level
#[poise::command(slash_command)]
pub async fn level(
    ctx: Context<'_>,
    #[description = "Selected user"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let Some(guild_id) = ctx.guild_id() else {
        ctx.say("This command can only be executed in a guild").await?;
        return Ok(());
    };
    let u = user.as_ref().unwrap_or_else(|| ctx.author());
    let id = ids_to_bytes(*guild_id.as_u64(), *u.id.as_u64());
    let user_id = *u.id.as_u64();
    let data = ctx.data();

    let (rank, (_, level)) = {
        if data.db.get_bytes_cf(&id, &data.level_cf).is_none() {
            (usize::MAX, (user_id, Level::default()))
        } else {
            let mut records: Vec<_> = data
                .db
                .guild_records(*guild_id.as_u64(), &data.level_cf)
                .expect("Internal DB error: Invalid CF")
                .collect();
            records.sort_unstable_by_key(|(uid, level)| level.xp as u32);
            records
                .into_iter()
                .rev()
                .enumerate()
                .find(|(i, (uid, _))| *uid == user_id)
                .unwrap_or_else(|| {
                    (
                        usize::MAX,
                        (
                            0,
                            Level {
                                xp: 0.0,
                                boost_factor: 1.1,
                            },
                        ),
                    )
                })
        }
    };
    let Some(cursor) = level_embed(&data,
&format!("{}#{}",u.name, u.discriminator),
        &level.get_level().0.to_string(),
        level.xp,
        Level::xp_for_next_level(level.xp as u32),
        if rank == usize::MAX {
            "no XP".to_string()
        } else {
            (rank + 1).to_string()
        },
        u.face()).await else {
        ctx.send(|b| b.content("Internal error").ephemeral(true))
            .await?;
        return Ok(())

    };
    // ctx.author_member().await.unwrap().face()
    // ctx.channel_id().send_files(http, files, f)
    ctx.send(|b| {
        b.attachment(serenity::AttachmentType::Bytes {
            data: std::borrow::Cow::Owned(cursor.into_inner()),
            filename: "image.png".to_string(),
        })
    })
    .await;
    // let response = format!("User:{}\nLevel: {}\nXp: {}/{}\nRank: {}",);
    // ctx.say(response).await?;
    Ok(())
}

const PAGESIZE: usize = 10;

/// Displays the XP server leaderboard
#[poise::command(slash_command)]
pub async fn leaderboard(
    ctx: Context<'_>,
    #[description = "Leaderboard page"] page: Option<u16>,
) -> Result<(), Error> {
    let Some(guild_id) = ctx.guild_id() else {
        ctx.say("This command can only be executed in a guild").await?;
        return Ok(());
    };
    let mut page = (page.unwrap_or(1).max(1) - 1) as usize;
    let data = ctx.data();
    let mut records: Vec<_> = data
        .db
        .guild_records(*guild_id.as_u64(), &data.level_cf)
        .expect("Internal DB error: invalid CF")
        .collect();
    if page * PAGESIZE + 1 > records.len() {
        ctx.send(|b| b.ephemeral(true).content("No ranks to see here"))
            .await;
        return Ok(());
    }
    let start = Instant::now();
    let cooldown = Duration::from_secs(120);
    records.sort_unstable_by_key(|(uid, level)| level.xp as u32);
    let guild = ctx.partial_guild().await.ok_or("Failed to open guild")?;
    let author = ctx.author();

    let mut embed = CreateEmbed::default();
    create_leaderboard_embed(ctx, &mut embed, &records, page, &guild, data, author).await;

    let msg = ctx
        .send(|b| {
            b.components(|f| {
                f.create_action_row(|row| {
                    row.create_button(|button| {
                        button
                            .label("⬅️")
                            .style(ButtonStyle::Secondary)
                            .custom_id("prev")
                    });
                    row.create_button(|button| {
                        button
                            .label("➡️")
                            .style(ButtonStyle::Secondary)
                            .custom_id("next")
                    });
                    row.create_button(|button| {
                        button
                            .label("⏮️")
                            .style(ButtonStyle::Secondary)
                            .custom_id("start")
                    })
                })
            });
            b.embeds.push(embed);
            b
        })
        .await
        .unwrap();
    // msg.into_message().await.unwrap().await_component_interaction(shard_messenger)
    while let Some(command) = msg
        .message()
        .await
        .unwrap()
        .await_component_interaction(ctx)
        .timeout(cooldown.saturating_sub(start.elapsed()))
        .author_id(author.id)
        .await
    {
        let new_page = match command.data.custom_id.as_str() {
            "prev" => page.max(2) - 1,
            "next" => page + 1,
            _ => 1,
        };
        if new_page == page {
            continue;
        }
        let mut embed = CreateEmbed::default();
        if create_leaderboard_embed(ctx, &mut embed, &records, page, &guild, data, author)
            .await
            .is_none()
        {
            continue;
        };
        page = new_page;
        command
            .create_interaction_response(ctx, |x| {
                x.kind(serenity::InteractionResponseType::UpdateMessage)
                    // .interaction_response_data(|f| f.set_embed())
                    .interaction_response_data(|f| f.set_embed(embed))
            })
            .await
            .unwrap();
        // command
        //     .edit_original_interaction_response(ctx, |x| {
        //         x.set_embed({
        //             let mut embed = CreateEmbed::default();
        //             embed.title(format!("works! id: {}", command.as_ref().id));
        //             embed
        //         })
        //     })
        //     .await
        //     .unwrap();
        // ctx.send(|b| b.content("hello!")).await;
    }
    Ok(())
}

async fn create_leaderboard_embed<'a>(
    ctx: Context<'a>,
    mut embed: &'a mut CreateEmbed,
    records: &'a Vec<(u64, Level)>,
    page: usize,
    guild: &'a PartialGuild,
    data: &'a Data,
    author: &User,
) -> Option<&'a mut CreateEmbed> {
    if page * PAGESIZE + 1 > records.len() {
        return None;
    };
    embed.title("Leaderboard");
    // embed.description("");
    for (i, (user_id, level)) in records
        .iter()
        .rev()
        .enumerate()
        .skip(page * PAGESIZE)
        .take(PAGESIZE)
    {
        let level_parsed = level.get_level();
        embed.field(
            guild
                .member(ctx, *user_id)
                .await
                .map(|x| format!("{}. {}", i + 1, x.display_name()))
                .unwrap_or_default()
                + if user_id == author.id.as_u64() {
                    " ~ You"
                } else {
                    ""
                },
            format!("Level: {}\nTotal XP: {}", level_parsed.0, level.xp),
            false,
        );
    }
    format_embed::<&str>(&mut embed, Some(ctx), None, data);
    Some(embed)
}
