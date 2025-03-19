# AI Prompts

PyCharm has a built in AI Assistant which can be used to boost your DX.

This is a collection of prompts to be used and extended when working on this project.

## Commit Message Prompt

Generate a concise and informative commit message adhering to the Conventional Commits format, but omit the scope.

Start with a short, imperative sentence (maximum 50 characters) summarizing the primary change. Do not use backticks to wrap the message.

Leave an empty line after the summary.

Follow with a more detailed explanation in 2-3 sentences.

If applicable, add a bullet-point list of specific changes, keeping each point brief and to the point.

Avoid overly verbose descriptions or unnecessary details. Focus on the 'what' and 'why' of the changes.

Example:

fix: Correct login authentication

Addresses issue with incorrect password validation.

- Updated password check logic.
- Improved error message clarity.