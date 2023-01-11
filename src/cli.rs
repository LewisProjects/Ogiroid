pub use clap::Parser;

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
        env = "BOT_ACTIVITY",
        default_value = "with no one"
    )]
    /// The Discord token of the bot to connect to
    pub activity: String,
    #[arg(short, long, env = "CHANNEL_CACHE_SIZE", default_value = "20")]
    /// The amount of messages to cache per channel
    pub cache_size: usize,
    #[arg(short, long, env = "EDIT_CACHE_SIZE", default_value = "100")]
    /// The maximum amount of message edits to remember.
    pub edit_cache: u32,
    #[arg(short, long, env = "DELETION_CACHE_SIZE", default_value = "100")]
    /// The maximum amount of message deletions to remember.
    pub deletion_cache: u32,
    #[arg(short, long, env = "LOCAL_GUILD_ID")]
    /// The guild id to register commands locally in, commands registered globally if unset
    pub guild_id: Option<u64>,
}
