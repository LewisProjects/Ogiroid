use std::borrow::Cow;
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
    Mentionable, MessageBuilder, PartialGuild, User,
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
use turborand::rng::Rng;
use turborand::TurboRand;

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

    pub fn incrase_xp(&mut self, msg_len: usize) -> Option<u32> {
        let rand = Rng::new();
        let (level, next_level_xp) = self.get_level();
        if rand.sample(&[0, 1, 2]).unwrap() != &0 {
            return None;
        }
        self.xp += *{
            if msg_len < 50 {
                rand.sample(&POSSIBLE_XP[..30])
            } else {
                rand.sample(&POSSIBLE_XP)
            }
        }
        .unwrap() as f32
            * self.boost_factor;
        if next_level_xp > 4 && self.xp >= next_level_xp as f32 {
            Some(level + 1)
        } else {
            None
        }
    }

    pub fn get_level(&self) -> (u32, u32) {
        let xp = self.xp as u32;
        let (level, _) = LEVELS
            .iter()
            .take_while(|&&x| x <= xp)
            .enumerate()
            .last()
            .unwrap_or((0, &0));
        (level as u32, LEVELS.get(level + 1).map(|x| *x).unwrap_or(0))
    }
    pub fn xp_for_next_level(level: usize) -> u32 {
        LEVELS.get(level + 1).map(|x| *x).unwrap_or(0)
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
    if let Some(last_message) = data.cooldown.get(&id) {
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
    let levelup = level.incrase_xp(message.content.len());
    data.db.put_cf(&id, level, &data.level_cf)?;
    if let Some(new_level) = levelup {
        message
            .reply(
                ctx,
                MessageBuilder::default()
                    .push(
                        message
                            .author
                            .nick_in(ctx, message.guild_id.unwrap())
                            .await
                            .map(|x| Cow::Owned(x))
                            .unwrap_or(Cow::Borrowed(&message.author.name.clone())),
                    )
                    .push(" has leveled up to level ")
                    .push(new_level)
                    .push("! WOOOOOOOOOOOO")
                    .build(),
            )
            .await;
    };
    Ok(())
}

/// Sets a user's XP
#[poise::command(slash_command, required_permissions = "MODERATE_MEMBERS")]
pub async fn set_level(
    ctx: Context<'_>,
    #[description = "new XP"] xp: f32,
    #[description = "Selected user"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let Some(guild_id) = ctx.guild_id() else {
        ctx.say("This command can only be executed in a guild").await?;
        return Ok(());
    };
    let u = user.as_ref().unwrap_or_else(|| ctx.author());
    let data = ctx.data();
    let id = ids_to_bytes(*guild_id.as_u64(), *u.id.as_u64());
    let boost_factor = if let Some(level) = data.db.get_cf(&id, &data.level_cf) {
        level.boost_factor
    } else {
        1.0
    };
    data.db
        .put_cf(&id, Level { xp, boost_factor }, &data.level_cf)
        .unwrap();
    ctx.send(|b| {
        b.embed(|embed| {
            let mut embed = embed
                .title("Success")
                .description(format!("Successfully set {}'s XP to {}", u.name, xp));
            format_embed::<&str>(&mut embed, Some(ctx), None, data);
            embed
        })
    });
    Ok(())
}

/// Sets a user's boost factor(XP multiplier)
#[poise::command(slash_command, required_permissions = "MODERATE_MEMBERS")]
pub async fn set_xp_booster(
    ctx: Context<'_>,
    #[description = "boost level(1.0 is no boost level)"] boost_factor: f32,
    #[description = "Selected user"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let Some(guild_id) = ctx.guild_id() else {
        ctx.say("This command can only be executed in a guild").await?;
        return Ok(());
    };
    let u = user.as_ref().unwrap_or_else(|| ctx.author());
    let data = ctx.data();
    let id = ids_to_bytes(*guild_id.as_u64(), *u.id.as_u64());
    let xp = if let Some(level) = data.db.get_cf(&id, &data.level_cf) {
        level.xp
    } else {
        0.0
    };
    data.db
        .put_cf(&id, Level { xp, boost_factor }, &data.level_cf);
    Ok(())
}

/// Displays a user's level, XP and rank
#[poise::command(slash_command, aliases("rank", "xp"))]
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
    let ((level, next_level_xp), xp) = (level.get_level(), level.xp);
    let Some(cursor) = level_embed(&data,
&format!("{}#{}",u.name, u.discriminator),
        &level.to_string(),
        xp,
        next_level_xp,
        if rank == usize::MAX {
            "None".to_string()
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

const LEVELS: [u32; 151] = [
    0, 100, 255, 475, 770, 1_150, 1_625, 2_205, 2_900, 3_720, 4_675, 5_775, 7_030, 8_450, 10_045,
    11_825, 13_800, 15_980, 18_375, 20_995, 23_850, 26_950, 30_305, 33_925, 37_820, 42_000, 46_475,
    51_255, 56_350, 61_770, 67_525, 73_625, 80_080, 86_900, 94_095, 101_675, 109_650, 118_030,
    126_825, 136_045, 145_700, 155_800, 166_355, 177_375, 188_870, 200_850, 213_325, 226_305,
    239_800, 253_820, 268_375, 283_475, 299_130, 315_350, 332_145, 349_525, 367_500, 386_080,
    405_275, 425_095, 445_550, 466_650, 488_405, 510_825, 533_920, 557_700, 582_175, 607_355,
    633_250, 659_870, 687_225, 715_325, 744_180, 773_800, 804_195, 835_375, 867_350, 900_130,
    933_725, 968_145, 1_003_400, 1_039_500, 1_076_455, 1_114_275, 1_152_970, 1_192_550, 1_233_025,
    1_274_405, 1_316_700, 1_359_920, 1_404_075, 1_449_175, 1_495_230, 1_542_250, 1_590_245,
    1_639_225, 1_689_200, 1_740_180, 1_792_175, 1_845_195, 1_899_250, 1_954_350, 2_010_505,
    2_067_725, 2_126_020, 2_185_400, 2_245_875, 2_307_455, 2_370_150, 2_433_970, 2_498_925,
    2_565_025, 2_632_280, 2_700_700, 2_770_295, 2_841_075, 2_913_050, 2_986_230, 3_060_625,
    3_136_245, 3_213_100, 3_291_200, 3_370_555, 3_451_175, 3_533_070, 3_616_250, 3_700_725,
    3_786_505, 3_873_600, 3_962_020, 4_051_775, 4_142_875, 4_235_330, 4_329_150, 4_424_345,
    4_520_925, 4_618_900, 4_718_280, 4_819_075, 4_921_295, 5_024_950, 5_130_050, 5_236_605,
    5_344_625, 5_454_120, 5_565_100, 5_677_575, 5_791_555, 5_907_050, 6_024_070, 6_142_625,
];
const POSSIBLE_XP: [u8; 101] = [
    10, 10, 10, 10, 11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 15,
    16, 16, 16, 16, 17, 17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 19, 20, 20, 20, 20, 21, 21, 21, 21,
    22, 22, 22, 22, 23, 23, 23, 23, 24, 24, 24, 24, 25, 25, 26, 26, 27, 27, 28, 28, 29, 29, 30, 30,
    31, 31, 32, 32, 33, 33, 34, 34, 35, 35, 36, 36, 37, 37, 38, 38, 39, 39, 40, 41, 42, 43, 44, 45,
    46, 47, 48, 49, 50,
];
