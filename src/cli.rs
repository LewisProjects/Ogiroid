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
}
