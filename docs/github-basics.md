# Using this repository — GitHub basics

A **repository** is the project's folder and recorded history on GitHub. You can read and download this public repository without installing Git or creating an account.

## Read and download

- The main page displays `README.md`, the starting guide.
- Click a file or folder to open it. Use your browser's Back button to return.
- Click **Code → Download ZIP** to download a copy. Extract it before following commands.
- A file you change on your own computer does not automatically change GitHub or your Pi.

## Four useful words

| Term | Meaning |
| --- | --- |
| Commit | A saved set of changes with a short description |
| Branch | A separate line of work, useful for trying changes |
| Pull request | A proposed change that can be reviewed before it is merged |
| Issue | A report, question or suggestion about the project |

## Report a problem

Open the repository's **Issues** tab and choose **New issue**. Describe what you tried, what you expected, what actually happened, your Pi/display models and Batocera version. Include relevant log lines, but remove passwords and personal connection information. A GitHub account is required to post.

## Small documentation edits in the browser

If you own the repository, open a Markdown file and use GitHub's pencil/edit button. Make the change, preview the formatting and choose **Commit changes**. Use a short English description such as `Clarify the SSH connection step`.

For changes to working code, make a branch and pull request rather than experimenting directly in the main version. Run tests and try the change on the real device before claiming it works on hardware.

## Before updating the Pi

Check what changed on GitHub, keep a backup of the working Pi files, then follow the [update instructions](troubleshooting.md#update-the-oled-software). GitHub does not remotely install updates on your console.
