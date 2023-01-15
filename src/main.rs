#![allow(dead_code, unused)]
use crate::image_utils::create_level_image;
mod image_utils;
use image::{ImageBuffer, Rgba};
use rocksdb::BoundColumnFamily;
use rusttype::Font;
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
    deleted_cache: Box<AsyncCache<u64, SnipeDel>>,
    edit_cache: Box<AsyncCache<u64, Snipe>>,
    cache: Arc<Cache>,
    db: Db,
    cooldown: Box<AsyncCache<u64, Instant>>,
    color: (u8, u8, u8),
    level_image: Box<ImageBuffer<Rgba<u8>, Vec<u8>>>,
    font: Font<'static>,
    font_width: f32,
    http_client: reqwest::Client,
    level_cf: Box<String>,
    server_cf: Box<String>,
} // User data, which is stored and accessible in all command invocations
pub type Error = Box<dyn std::error::Error + Send + Sync>;
pub type Context<'a> = poise::Context<'a, Data, Error>;

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    unsafe {
        let mut total: u32 = 0;
        for (i, xp) in LEVELS.iter().enumerate() {
            total += xp;
            LEVELS_TOTALXP[i] = total
        }
    };
    let framework = poise::Framework::builder()
        .options(poise::FrameworkOptions {
            commands: vec![
                level(),
                editsnipe(),
                snipe(),
                leaderboard(),
                set_level(),
                set_xp_booster(),
            ],
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
                let font_file = if let Some(path) = cli.font {
                    std::fs::read(path).unwrap()
                } else {
                    include_bytes!("../assets/OpenSans-Regular.ttf").to_vec()
                };
                let font_bold =
                    Font::try_from_bytes(include_bytes!("../assets/OpenSans-Bold.ttf")).unwrap();
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
                let font = Font::try_from_vec(font_file).unwrap();

                let db = Db::new(
                    cli.db_path
                        .to_str()
                        .expect("--db-path needs to be valid unicode"),
                    cli.level_cache_size,
                    &[cli.level_cf.clone(), cli.server_cf.clone()],
                )
                .unwrap();

                Ok(Data {
                    font_width: cli.font_width,
                    color,
                    level_image: Box::new(create_level_image(&font_bold, cli.corner_radius)),
                    font,
                    db,
                    level_cf: Box::new(cli.level_cf),
                    server_cf: Box::new(cli.server_cf),
                    edit_cache: Box::new(
                        AsyncCache::new(
                            cli.edit_cache as usize * 50,
                            cli.edit_cache as i64 * 1024,
                            tokio::spawn,
                        )
                        .unwrap(),
                    ),

                    cooldown: Box::new(AsyncCache::new(500, 1000, tokio::spawn).unwrap()),
                    deleted_cache: Box::new(
                        AsyncCache::new(
                            cli.deletion_cache as usize * 50,
                            cli.deletion_cache as i64 * 1024,
                            tokio::spawn,
                        )
                        .unwrap(),
                    ),
                    cache: ctx.cache().unwrap().clone(),
                    http_client: reqwest::Client::new(),
                })
            })
        });

    framework.run().await.unwrap();
}
