#![allow(dead_code, unused)]
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
mod state;
use state::{DBFailure, Db};
use tokio::time::Instant;

pub struct Data {
    deleted_cache: AsyncCache<u64, SnipeDel>,
    edit_cache: AsyncCache<u64, Snipe>,
    cache: Arc<Cache>,
    db: Db,
    cooldown: AsyncCache<u64, Instant>,
    color: (u8, u8, u8),
} // User data, which is stored and accessible in all command invocations
pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![level(), editsnipe(), snipe(), leaderboard()],
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
                let len = cli.color_string.len();
                if !matches!(len, 3 | 6) {
                    panic!("--color only accepts a string in the format of `FFFFFF`")
                };
                let mut colors = (0..=2).map(|i| {
                    u8::from_str_radix(&cli.color_string[(i * 2)..][..2], 16)
                        .expect("encountered non-HEX chars when parsing the value of --color")
                });
                let color = (
                    colors.next().unwrap(),
                    colors.next().unwrap(),
                    colors.next().unwrap(),
                );
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
                let activity = cli.activity_type.activity(&cli.activity, cli.stream_url);
                ctx.set_activity(activity).await;
                ctx.cache.set_max_messages(cli.cache_size);

                Ok(Data {
                    color,
                    db: Db::new(
                        cli.db_path
                            .to_str()
                            .expect("--db-path needs to be valid unicode"),
                        cli.level_cache_size,
                    )
                    .unwrap(),
                    edit_cache: AsyncCache::new(1000, cli.edit_cache as i64 * 1024, tokio::spawn)
                        .unwrap(),

                    cooldown: AsyncCache::new(1000, 10000, tokio::spawn).unwrap(),
                    deleted_cache: AsyncCache::new(
                        1000,
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
