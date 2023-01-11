use crate::Data;
use poise::serenity_prelude::Context;
use poise::{event::Event, FrameworkContext};
use std::error::Error;
pub async fn handle_event<'a, E>(
    ctx: &'a Context,
    event: &'a Event<'_>,
    framework_ctx: FrameworkContext<'a, Data, Box<dyn Error + Send + Sync>>,
    data: &'a Data,
) -> Result<(), E> {
    use Event::*;
    match event {
        MessageUpdate {
            old_if_available,
            new,
            event,
        } => {
            if let Some(old) = old_if_available {
                let safe = old.content_safe(&ctx.cache);
                data.edit_cache
                    .insert(*event.channel_id.as_u64(), safe, 5)
                    .await;
            }
        }
        MessageDelete {
            channel_id,
            deleted_message_id,
            guild_id,
        } => {
            println!("{} {} {:?}", channel_id, deleted_message_id, guild_id)
        }
        GuildMemberAddition { new_member } => {
            println!("new member: {new_member}")
        }

        _ => (),
    };
    Ok(())
}
