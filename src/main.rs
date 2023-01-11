use std::sync::Arc;
use stretto::AsyncCache;

use poise::serenity_prelude::{
    self as serenity, ActivityButton, CacheHttp, CreateButton, GuildId, MessageActivity,
};
mod cli;
use cli::{Cli, Parser};
use serenity::cache::Cache;
mod event;
use event::handle_event;
mod commands;
use commands::*;
mod util;

pub struct Data {
    deleted_cache: AsyncCache<u64, SnipeDel>,
    edit_cache: AsyncCache<u64, Snipe>,
    cache: Arc<Cache>,
} // User data, which is stored and accessible in all command invocations
pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;

/// Displays your or another user's account creation date
#[poise::command(slash_command)]
async fn age(
    ctx: Context<'_>,
    #[description = "Selected user"] user: Option<serenity::User>,
) -> Result<(), Error> {
    let u = user.as_ref().unwrap_or_else(|| ctx.author());
    let response = format!("{}'s account was created at {}", u.name, u.created_at());
    ctx.say(response).await?;
    Ok(())
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![age(), editsnipe(), snipe()],
            event_handler: |ctx, event, framework_context, data| {
                Box::pin(handle_event(ctx, event, framework_context, data))
            },
            ..Default::default()
        })
        .token(cli.token)
        .intents(
            serenity::GatewayIntents::non_privileged() | serenity::GatewayIntents::MESSAGE_CONTENT,
        )
        .setup(move |ctx, _ready, framework| {
            Box::pin(async move {
                println!(
                    "Bot connected as {}",
                    ctx.http.get_current_user().await.unwrap().name
                );
                if let Some(guild) = cli.guild_id {
                    let Some(guild) = GuildId(guild).to_guild_cached(&ctx.cache) else {
                    panic!("Failed to get guild with id {}", guild)
                };
                    poise::builtins::register_in_guild(
                        ctx,
                        &framework.options().commands,
                        guild.id,
                    )
                    .await?;
                    println!("Registered commands locally in guild {}", guild.name);
                } else {
                    poise::builtins::register_globally(ctx, &framework.options().commands).await?;
                    println!("Registered commands globally")
                }
                ctx.dnd().await;
                println!("Set activity to {} {}", cli.activity_type, cli.activity);
                let activity = cli
                    .activity_type
                    .activity(&cli.activity_type, cli.stream_url);
                ctx.set_activity(activity).await;
                ctx.cache.set_max_messages(cli.cache_size);
                Ok(Data {
                    edit_cache: AsyncCache::new(2000, cli.edit_cache as i64 * 1024, tokio::spawn)
                        .unwrap(),
                    deleted_cache: AsyncCache::new(
                        2000,
                        cli.deletion_cache as i64 * 1024,
                        tokio::spawn,
                    )
                    .unwrap(),
                    cache: ctx.cache().unwrap().clone(),
                })
            })
        });

    framework.run().await.unwrap();
}
