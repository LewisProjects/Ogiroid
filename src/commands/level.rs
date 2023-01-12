use std::error::Error as err;
use std::time::Duration;

use crate::state::{ids_to_bytes, DBFailure};
use crate::{Data, Db};
// use byteorder::{ByteOrder, LittleEndian};
use crate::format_embed;
use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use bytecheck::CheckBytes;
use poise::serenity_prelude::{CacheHttp, Context as DefContext, CreateEmbed};
use poise::serenity_prelude::{Message, MessageType};
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::DB;
use tokio::time::Instant;

#[derive(Archive, Deserialize, Serialize, Debug, PartialEq)]
#[archive_attr(derive(CheckBytes, Debug))]
pub struct Level {
    pub xp: f32,
    pub boost_factor: f32,
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
    pub fn xp_for_next_level(_xp_rem: u32) -> u32 {
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
    if let Some(last_message) = data.cooldown.get(&id) {
        let duration_since = last_message.as_ref().elapsed();
        if duration_since <= cooldown {
            return Ok(());
        }
    };
    data.cooldown.insert(id, Instant::now(), 50).await;
    let id = ids_to_bytes(
        *message.guild_id.unwrap().as_u64(),
        *message.author.id.as_u64(),
    );
    let Some(mut level) = data.db.get(&id) else {
        let mut level = Level::new(0.0, None);
        level.incrase_xp(message.content.len());
        data.db.put(&id, level)?;
        return Ok(())
    };
    level.incrase_xp(message.content.len());
    data.db.put(&id, level)?;
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
    let id = ids_to_bytes(*guild_id.as_u64(), *ctx.author().id.as_u64());
    let u = user.as_ref().unwrap_or_else(|| ctx.author());
    let data = ctx.data();
    let level = data.db.get(id).map(|x| x.get_level()).unwrap_or((0, 0));
    let response = format!(
        "{}'s current level is {}, with {}/{} xp",
        u.name,
        level.0,
        level.1,
        Level::xp_for_next_level(level.1),
    );
    ctx.say(response).await?;
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
    let page = (page.unwrap_or(1).max(1) - 1) as usize;
    let data = ctx.data();
    let mut records = data
        .db
        .db
        .prefix_iterator(guild_id.as_u64().to_le_bytes())
        .filter_map(|x| {
            if let Ok((key, value)) = x {
                let Ok(entry) = (unsafe {rkyv::from_bytes_unchecked::<Level>(&value)}) else {
            return None
        };
                let mut keyarr = [0u8; 8];
                keyarr.copy_from_slice(&key[8..]);
                Some((u64::from_le_bytes(keyarr), entry))
            } else {
                None
            }
        })
        .collect::<Vec<_>>();
    if page * PAGESIZE + 1 > records.len() {
        ctx.send(|b| b.ephemeral(true).content("No ranks to see here"))
            .await;
        return Ok(());
    }
    records.sort_unstable_by_key(|(uid, level)| level.xp as u32);
    let guild = ctx.partial_guild().await.unwrap();

    let mut embed = CreateEmbed::default();
    embed.title("Leaderboard");
    for (i, (user_id, level)) in records
        .into_iter()
        .rev()
        .enumerate()
        .skip(page * PAGESIZE)
        .take(10)
    {
        let level_parsed = level.get_level();
        embed.field(
            guild
                .member(ctx, user_id)
                .await
                .map(|x| format!("{}. {}", i + 1, x.display_name()))
                .unwrap_or_default()
                + if user_id == *ctx.author().id.as_u64() {
                    " ~ You"
                } else {
                    ""
                },
            format!("Level: {}\nTotal XP: {}", level_parsed.0, level.xp),
            false,
        );
    }
    format_embed::<&str>(&mut embed, Some(ctx), None);
    ctx.send(|b| {
        b.embeds.push(embed);
        b
    })
    .await;
    Ok(())
}
