pub use clap::Parser;
use std::num::NonZeroUsize;

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
    #[arg(short, long, env = "SIZE", default_value = "20")]
    /// The amount of messages to cache per channel
    pub cache_size: usize,
    #[arg(short, long, env = "SIZE", default_value = "100")]
    /// The maximum amount of message edits to remember.
    pub edit_cache: NonZeroUsize,
}
