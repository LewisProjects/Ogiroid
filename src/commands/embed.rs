use poise::serenity_prelude::{CreateEmbed, Timestamp};

use crate::Context;

pub fn format_embed<'a, T>(
    embed: &'a mut CreateEmbed,
    ctx: Option<Context<'a>>,
    timestamp: Option<T>,
) -> &'a mut CreateEmbed
where
    T: Into<Timestamp>,
{
    if let Some(timestamp) = timestamp {
        embed.timestamp(timestamp)
    } else {
        embed.timestamp(Timestamp::now())
    };
    if let Some(ctx) = ctx {
        let author = ctx.author();
        embed.footer(|footer| footer.text(&author.name).icon_url(author.face()));
    };
    embed.color((192, 202, 245));
    embed
}
