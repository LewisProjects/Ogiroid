use crate::commands::{handle_new_message, save_deleted, save_edit};
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
        Message { new_message } => {
            let _ = handle_new_message(ctx, data, new_message).await;
        }
        MessageUpdate {
            old_if_available,
            new,
            event,
        } => {
            save_edit(ctx, old_if_available, new, event, data).await;
        }
        MessageDelete {
            channel_id,
            deleted_message_id,
            guild_id,
        } => {
            save_deleted(
                ctx,
                data.cache.message(channel_id, deleted_message_id),
                channel_id,
                data,
            )
            .await
        }
        GuildMemberAddition { new_member } => {
            println!("new member: {new_member}")
        }

        _ => (),
    };
    Ok(())
}
