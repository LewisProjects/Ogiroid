use crate::serenity;
use crate::Context;
use crate::Data;
use crate::Error;
/// Displays your or another user's account creation date
#[poise::command(slash_command)]
pub async fn snipedit(
    ctx: Context<'_>,
    #[description = "Channel"] channel: Option<serenity::ChannelId>,
) -> Result<(), Error> {
    println!("{channel:?}");
    let c = channel.unwrap_or_else(|| ctx.channel_id());
    println!("{c:?}");
    let data = ctx.data();
    let Some(message) = data.edit_cache.get(c.as_u64()) else {
        ctx.say("could not find an edit to snipe").await;
        return Ok(())
    };
    ctx.say(message.as_ref()).await;
    Ok(())
}
