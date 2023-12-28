# Contributing to Ogiroid 🤝!
🎊👏 Firstly, thank you so much for taking out time to contribute to Ogiroid! 👏🎊

The following is a set of guidelines for contributing to Ogiroid, which is a part of [Lewis Projects](https://github.com/LewisProjects/) on GitHub. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

### Table of Contents:
1. [Code of Conduct](#code-of-conduct)
2. [What do I require before getting started?](#prerequisites)
3. [What can I do to contribute?](#contribution)
4. [Additional Notes]()

<hr>

## [Code of Conduct](#code-of-conduct)
> This project and everyone participating in it is governed by the Ogiroid code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the developers.

## [What do I require before getting started?](#prerequisites)
We expect you to be experienced with [Python](https://www.python.org/) and [Disnake](https://disnake.dev/) (a fork of [Discord.py](https://github.com/Rapptz/discord.py)). Having experience with Discord.py should also get you sailing, disnake and discord.py are almost the same, or you could also take a look at the very helpful disnake documentation.

## [What can I do to contribute?](#contribution) 
**1. Reporting any bugs 🐞:**

Cannot emphasize enough how much bug reporting/bug fixing helps us! It saves us numerous hours of painful code scouting. So you might ask yourself, how do I submit a bug report for Ogiroid? Quite simple honestly! First of all, did you:
+ Come across a bug while using the Discord bot? 
+ Come across a bug in the code?

**Case 1: While using the Discord Bot:**

You need to headover to a channel in [Lewis' Menelaws discord server](https://discord.com/5uw4eCQf6Z) and then type: ``/reportbug``, you will then be greeted by a modal looking something like this:

![MODAL](https://cdn.discordapp.com/attachments/1005117336761675847/1007706426896040077/unknown.png)

Fill this form & click **submit**. Our developer team will then recieve your bug report, we can then look into it 😇! Thank you!

**Case 2: A bug in the code (hmmm... quite rare 😜):**

You can raise an [issue](https://github.com/LewisProjects/Ogiroid/issues) and we will look into it. Please ensure you follow the proper [format we have](#) and be as specific as you can while reporting a bug. Obviously, there can be somee cases where the format might not be as important as in other cases, please use your judgement in such cases.

Alternatively, you can headover to our [Discord Server](https://discord.com/5uw4eCQf6Z) and report the bug using the first method (scroll up if you missed it).

**__📚📚 Bug Reporting Guidelines 📚📚:__**

+ Please refrain from reporting your bug multiple times, this will lead to us blacklisting you (and potentially banning you permanently on the Discord server) 😒.
+ Please check all the [issues](https://github.com/LewisProjects/Ogiroid/issues) before posting your bug, your bug report could really just be a duplicate 👀!
+ Please ensure you be as specific as you can, this saves us a ton of time ⌚.
+ Please use your right judgement 🎓. 

With that being said, you have officially reported a bug! Thank you so much 🤩!

<!--Contributing.md: writeup #1-->

### Contributing Code

<hr>

#### Get the repository

Fork the repository and then clone it using: (make sure to insert your username)

```git clone https://github.com/YOURGITHUBUSERNAME/Ogiroid.git```

After this get into the folder you cloned the repository to.
We always work on the development branch so make sure you are on the dev branch.

```git checkout development```

Now you need to create a Discord Bot if you don't already have one. Please look up a guide for how to do this.
Invite the bot to a test server you own or create a test server.

Now copy secrets.env.template and rename the copy to secrets.env
Insert your bots token in the correct field.
Add a postgres database URL we use a database from neon.tech for testing you can use a local database.
Set development to true. The rest can be ignored for now.

#### Install the requirements

To install the requirements:

```pip install -r requirements.txt```

#### Run the Bot

And finally to run the bot:

```python main.py```

utils/CONSTANTS.py stores the ids for various channels, for the main server and for the official development server, to wich you will gain access after a significant contribution. 

Use ```black . --safe``` for formatting (need to install black with pip)

#### Database Migrations

```alembic revision --autogenerate```

```alembid upgrade head```

#### Help

If you need any help contact us on discord or open an issue.

After you have finished writing the code open a PR with the base branch being development.
