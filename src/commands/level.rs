use crate::state::ids_to_bytes;
use crate::{Data, Db};
// use byteorder::{ByteOrder, LittleEndian};
use crate::serenity;
use crate::Arc;
use crate::Context;
use crate::Error;
use bytecheck::CheckBytes;
use poise::serenity_prelude::{Message, MessageType};
use rkyv::de::deserializers::SharedDeserializeMap;
use rkyv::validation::validators::DefaultValidator;
use rkyv::{Archive, Deserialize, Serialize};
use rocksdb::DB;

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

    pub fn incrase_xp(&mut self) {
        self.xp += 3.0 * self.boost_factor
    }

    pub fn get_level(&self) -> (u32, u16) {
        let xp = self.xp as u64;
        ((xp / 1000) as u32, (xp % 1000) as u16)
    }
}

pub fn handle_message(data: &Data, message: &Message) {
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
        return;
    }
    let id = ids_to_bytes(
        *message.guild_id.unwrap().as_u64(),
        *message.author.id.as_u64(),
    );
    let Some(mut level) = data.db.get(id) else {
        let mut level = Level::new(0.0, None);
        level.incrase_xp();
        data.db.put(id, level);
        return ()
    };
    level.incrase_xp();
    data.db.put(id, level);
    ()
}

/// Displays your or another user's account creation date
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
    let response = format!(
        "{}'s current XP is {}",
        u.name,
        ctx.data().db.get(id).map(|x| x.xp).unwrap_or(0.0)
    );
    ctx.say(response).await?;
    Ok(())
}
