use poise::serenity_prelude::Mentionable;

use crate::serenity;
use poise::serenity_prelude::Message;
use serenity::cache::Cache;
use std::fmt::Write;
use std::sync::Arc;
pub fn sanitize_message(message: Message, cache: &Arc<Cache>) -> String {
    // First replace all user mentions.
    let mut result = message.content;
    for u in &message.mentions {
        let mut at_distinct = String::with_capacity(38);
        at_distinct.push('@');
        at_distinct.push_str(&u.name);
        at_distinct.push('#');
        write!(at_distinct, "{:04}", u.discriminator).unwrap();

        let mut m = u.mention().to_string();
        // Check whether we're replacing a nickname mention or a normal mention.
        // `UserId::mention` returns a normal mention. If it isn't present in the message, it's a nickname mention.
        if !result.contains(&m) {
            m.insert(2, '!');
        }

        result = result.replace(&m, &at_distinct);
    }

    // Then replace all role mentions.
    for id in &message.mention_roles {
        let mention = id.mention().to_string();

        if let Some(role) = id.to_role_cached(&cache) {
            result = result.replace(&mention, &format!("@{}", role.name));
        } else {
            result = result.replace(&mention, "@deleted-role");
        }
    }

    // And finally replace everyone and here mentions.
    result
        .replace("@everyone", "@\u{200B}everyone")
        .replace("@here", "@\u{200B}here")
}
