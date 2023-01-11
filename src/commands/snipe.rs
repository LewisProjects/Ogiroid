use crate::serenity;
use crate::Data;

use crate::util::sanitize_message;
use crate::Context;
use crate::Error;
use diffy::create_patch;
use diffy::PatchFormatter;
use poise::serenity_prelude::Context as ContextEv;
use poise::serenity_prelude::Message;
use poise::serenity_prelude::MessageUpdateEvent;
use poise::serenity_prelude::UserId;
#[derive(Debug)]
pub struct Snipe {
    pub before: Message,
    pub after: Option<Message>,
    pub authorid: UserId,
}

pub async fn save_edit<'a>(
    ctx: &ContextEv,
    old: &Option<Message>,
    new: &Option<Message>,
    event: &MessageUpdateEvent,
    data: &'a Data,
) {
    // Abort if the author of the message is a bot.
    if let Some(true) = event.author.as_ref().map(|x| x.bot) {
        return ();
    };

    // Abort if the old version of the message isn't cached
    if let Some(old) = old {
        let text = old;

        let id = event.author.as_ref().unwrap().id;
        let cost = text.content.len() as i64;
        data.edit_cache
            .insert(
                *event.channel_id.as_u64(),
                Snipe {
                    before: text.clone(),
                    after: new.clone(),
                    authorid: id,
                },
                cost,
            )
            .await;
    }
}

/// Displays your or another user's account creation date
#[poise::command(slash_command)]
pub async fn editsnipe(
    ctx: Context<'_>,
    #[description = "Channel"] channel: Option<serenity::ChannelId>,
) -> Result<(), Error> {
    let c = channel.unwrap_or_else(|| ctx.channel_id());
    let data = ctx.data();
    let Some(message) = data.edit_cache.get(c.as_u64()) else {
        ctx.say(format!("Could not find any recent edits in <#{}>", c.0)).await;
        return Ok(())
    };
    ctx.send(|b| {
        b.embed(|embed| {
            let mut embed = embed
                .author(|a| {
                    let author = ctx.author();
                    let mut build = a.name(&author.name);
                    if let Some(url) = author.avatar_url() {
                        build.icon_url(url);
                    }
                    build
                })
                .field(
                    "Before",
                    sanitize_message(message.as_ref().before.clone(), &data.cache),
                    false,
                );
            if let Some(after) = message.as_ref().after.as_ref() {
                embed.field("After", sanitize_message(after.clone(), &data.cache), false);
            }
            embed
        })
    })
    .await;
    Ok(())
}
