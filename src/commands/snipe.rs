use std::str::from_utf8_unchecked;

use crate::serenity;
use crate::Data;

use crate::format_embed;
use crate::Context;
use crate::Error;
use poise::serenity_prelude::Context as ContextEv;
use poise::serenity_prelude::Message;
use poise::serenity_prelude::MessageUpdateEvent;
use serenity::model::id::ChannelId;

#[derive(Debug)]
pub struct Snipe {
    pub before: Message,
    pub after: Option<Message>,
}

#[derive(Debug)]
pub struct SnipeDel {
    pub message: Message,
}

pub async fn save_deleted<'a>(
    ctx: &ContextEv,
    message: Option<Message>,
    channel: &ChannelId,
    data: &'a Data,
) {
    let Some(message) = message else {
        return ()
    };
    // Abort if the author of the message is a bot.
    if message.author.bot {
        return ();
    };

    let cost = message.content.len() as i64;
    data.deleted_cache
        .insert(channel.0, SnipeDel { message }, cost)
        .await;
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
                },
                cost,
            )
            .await;
    }
}

/// Get the most recently edited message in a channel
#[poise::command(slash_command)]
pub async fn editsnipe(
    ctx: Context<'_>,
    #[description = "Channel"] channel: Option<serenity::ChannelId>,
) -> Result<(), Error> {
    let c = channel.unwrap_or_else(|| ctx.channel_id());
    let data = ctx.data();
    let Some(message) = data.edit_cache.get(c.as_u64()) else {
        ctx.say(format!("Could not find any recent edits in <#{}>", c.0)).await?;
        return Ok(())
    };
    let Snipe { before, after } = message.as_ref();
    ctx.send(|b| {
        b.embed(|embed| {
            let mut embed = embed.author(|a| {
                let author = &before.author;
                let mut build = a.name(&author.name);
                if let Some(url) = author.avatar_url() {
                    build.icon_url(url);
                }
                build
            });
            format_embed(&mut embed, Some(ctx), Some(ctx.created_at()), data);
            let before = before.content_safe(&data.cache);
            let mut chunks = before.as_bytes().chunks(1024);
            for (i, line) in chunks.enumerate() {
                embed.field(
                    if i == 0 { "Before" } else { "" },
                    unsafe { from_utf8_unchecked(&line) },
                    false,
                );
            }
            if let Some(after) = after.as_ref() {
                let after = after.content_safe(&data.cache);

                let mut chunks = after.as_bytes().chunks(1024);
                for (i, line) in chunks.enumerate() {
                    embed.field(
                        if i == 0 { "After" } else { "" },
                        unsafe { from_utf8_unchecked(&line) },
                        false,
                    );
                }
            }
            embed
        })
    })
    .await?;
    Ok(())
}
/// Get the latest deleted message in a channel
#[poise::command(slash_command)]
pub async fn snipe(
    ctx: Context<'_>,
    #[description = "Channel"] channel: Option<serenity::ChannelId>,
) -> Result<(), Error> {
    let c = channel.unwrap_or_else(|| ctx.channel_id());
    let data = ctx.data();
    let Some(snipe) = data.deleted_cache.get(c.as_u64()) else {
        ctx.say(format!("Could not find a recently deleted message in <#{}>", c.0)).await?;
        return Ok(())
    };
    let SnipeDel { message } = snipe.as_ref();
    ctx.send(|b| {
        b.embed(|embed| {
            let mut embed = embed
                .author(|a| {
                    let author = &message.author;
                    let mut build = a.name(&author.name);
                    if let Some(url) = author.avatar_url() {
                        build.icon_url(url);
                    }
                    build
                })
                .url("https://github.com/LewisProjects/Ogiroid")
                .description(message.content_safe(&data.cache));
            format_embed(&mut embed, Some(ctx), Some(message.timestamp), data);
            if let Some(attachment) = message.attachments.get(0) {
                embed.image(&attachment.url);
            }
            embed
        });
        message
            .attachments
            .iter()
            .skip(1)
            .take(3)
            .for_each(|attachment| {
                b.embed(|embed| {
                    embed
                        .url("https://github.com/LewisProjects/Ogiroid")
                        .image(&attachment.url)
                });
            });
        b
    })
    .await?;
    Ok(())
}
