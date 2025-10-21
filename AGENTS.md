# Guidelines for AI Agents

## Commit Message Guidelines

### Focus on the "Why", Not Just the "What"

When writing commit messages, **always explain why the change was made**, not just what was changed. The diff already shows what changed - the commit message should provide context and reasoning.

### The Importance of "Why"

The "why" is often harder to infer than the "what", and it requires proper documentation. Without it, future developers (including your future self) will struggle to understand:

- **Contextual Background**: Why was this change necessary? What problem or feature was being addressed?
- **Decision-Making Process**: What options were considered? Why was this particular solution chosen?
- **Implications and Considerations**: What are the potential impacts or limitations of this change? Were there any trade-offs?

### Benefits of Detailed Commit Messages

1. **Knowing Past Intentions**: You won't remember every change you worked on in a few months or years. Detailed messages from the past help you understand your own reasoning and make better decisions.

2. **Providing Context for Other Engineers**: Commit messages are a form of asynchronous communication. They help other engineers understand what was in your head when you made the change, especially if you're away or have left the team.

3. **Looking Back at Accomplishments**: Running `git log --author=name` provides a clear chronological list of all your contributions with high fidelity.

4. **Spreading Knowledge and Awareness**: Good commit messages help team members learn from each other and build awareness of what's being done, especially in remote-heavy environments.

5. **Focusing Code Changes**: Writing a commit message forces you to think about the work. If you can't write a concise explanation of what you're doing and why, maybe you need to reconsider the change or break it into smaller logical pieces.

6. **Information at Your Fingertips**: Git is at your fingertips throughout development. Having detailed information in commit messages is faster and more convenient than clicking through to external tickets or PRs.

### How NOT to Write Commit Messages

❌ **Bad**: Summarizing the changes
```
Update authentication logic
```

❌ **Bad**: Only linking to a ticket
```
Fix #123
```

The problem: These messages don't explain why the change was necessary. The diff shows what changed - you need to provide the context and reasoning.

✅ **Good**: Explaining the reasoning
```
Fix race condition in authentication flow

Users were occasionally getting logged out unexpectedly during page
navigation. This was caused by the auth token refresh happening
simultaneously with route changes, leading to a race condition where
the old token would sometimes override the refreshed one.

This change ensures token refresh completes before allowing navigation
to proceed, preventing the race condition.
```

### Guidelines

- Don't just link to tickets - that puts all the work on the reader to understand context
- Explain the problem being solved and why this solution was chosen
- Include relevant trade-offs or limitations if applicable
- Write for your future self and other engineers who may need to maintain this code
- Remember: the git log is a valuable learning resource and debugging tool

## Pull Request Description Guidelines

Pull request descriptions should follow the same principles as commit messages: **focus on the "why", not just the "what"**.

### What to Include in PR Descriptions

1. **Summary**: A concise overview of what the PR accomplishes and why it's needed
2. **Context**: Background information about the problem being solved or feature being added
3. **Approach**: Explanation of the solution chosen and why (especially if there were alternatives)
4. **Trade-offs**: Any known limitations, compromises, or technical debt introduced
5. **Testing**: How the changes were tested and what scenarios were covered
6. **Risks**: Any potential impacts on existing functionality or deployment considerations

### How NOT to Write PR Descriptions

❌ **Bad**: Minimal description
```
Fix bug
```

❌ **Bad**: Only ticket reference
```
Fixes #456
```

❌ **Bad**: Just listing changes
```
- Updated auth.py
- Modified login form
- Added new test
```

The problem: These descriptions don't provide context or reasoning. Reviewers and future maintainers need to understand why the changes were necessary.

✅ **Good**: Comprehensive description
```
Fix race condition in authentication flow

## Summary
Users were occasionally getting logged out unexpectedly during page navigation.
This PR fixes the race condition by ensuring token refresh completes before
navigation proceeds.

## Context
The issue occurred when the auth token refresh was triggered simultaneously
with route changes. The old token would sometimes override the refreshed one,
causing unexpected logouts.

## Approach
Added a mutex to ensure token refresh operations are atomic. Considered using
a queue-based approach but opted for the mutex solution due to its simplicity
and lower overhead.

## Testing
- Added unit tests for concurrent token refresh scenarios
- Manually tested rapid page navigation while token refresh was occurring
- Verified no performance regression with load testing

## Risks
Low risk - the mutex is only held briefly during token operations.
```

### Guidelines

- Treat PR descriptions as documentation for the changes
- Provide enough context that reviewers don't need to read every line of code to understand the change
- Explain your decision-making process, especially for non-obvious solutions
- Include test plan details so reviewers can verify the testing was thorough
- Remember: PR descriptions complement commit messages - use both effectively
