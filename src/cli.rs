use std::{fmt::Display, path::PathBuf};

pub use clap::Parser;
use poise::serenity_prelude::Activity;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
pub struct Cli {
    #[arg(short, long, value_name = "TOKEN", env = "DISCORD_TOKEN")]
    /// The Discord token of the bot to connect to
    pub token: String,
    #[arg(
        short,
        long,
        value_name = "ACTIVITY",
        env = "ACTIVITY",
        default_value = "your walls for you"
    )]
    /// The activity the bot should have
    pub activity: String,
    #[arg(short, long, env = "CHANNEL_CACHE_SIZE", default_value = "20")]
    /// The amount of messages to cache per channel
    pub cache_size: usize,
    #[arg(short, long, env = "EDIT_CACHE_SIZE", default_value = "200")]
    /// The maximum amount of message edits to remember. In KiB of storage
    pub edit_cache: u32,
    #[arg(short, long, env = "DELETION_CACHE_SIZE", default_value = "200")]
    /// The maximum amount of message deletions to remember. In KiB of storage
    pub deletion_cache: u32,
    #[arg(short, long, env = "LOCAL_GUILD_ID")]
    /// The guild id to register commands locally in, commands registered globally if unset
    pub guild_id: Option<u64>,
    /// Which tests to ignore, optional
    #[arg(
        short = 'z',
        long,
        value_enum,
        value_name = "ACTIVITY_TYPE",
        env = "ACTIVITY_TYPE",
        default_value = "watching"
    )]
    pub activity_type: ActivityType,

    #[arg(short, long, env = "STREAM_URL", default_value = "https://twitch.tv")]
    /// The stream URL to use, only applies when activity_type is set to streaming
    pub stream_url: String,
    #[arg(long, env = "DB_PATH", default_value = "db")]
    /// The path to the directory to use for storing the DB
    pub db_path: PathBuf,

    #[arg(long, env = "LEVEL_CACHE", default_value = "200")]
    /// The number of elements to keep in the LEVELLING DB cache
    pub level_cache_size: usize,
}

#[derive(clap::ValueEnum, Clone, Debug, PartialEq, PartialOrd, Eq)]
pub enum ActivityType {
    Listening,
    Competing,
    Playing,
    Watching,
    Streaming,
}

impl ActivityType {
    pub fn activity<N, U>(&self, name: N, stream_url: U) -> Activity
    where
        N: ToString,
        U: AsRef<str>,
    {
        match self {
            Self::Listening => Activity::listening(name),
            Self::Competing => Activity::competing(name),
            Self::Playing => Activity::playing(name),
            Self::Watching => Activity::watching(name),
            Self::Streaming => Activity::streaming(name, stream_url),
        }
    }
}

impl Display for ActivityType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let msg = match self {
            Self::Watching => "WATCHING",
            Self::Listening => "LISTENING TO",
            Self::Competing => "Competing in",
            Self::Playing => "PLAYING",
            Self::Streaming => "STREAMING",
        };
        write!(f, "{}", msg)
    }
}
