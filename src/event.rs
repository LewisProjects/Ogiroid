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
            println!(
                // "{:#?} {:#?} {:#?}",
                "{:?}",
                // data.cache
                //     .message(event.channel_id, event.id)
                //     .map(|x| x.content_safe(&data.cache)),
                old_if_available
                    .as_ref()
                    .map(|x| x.content_safe(&data.cache)),
                ctx.cache.message(channel_id, message_id) // new,
                                                          // event
            );
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
