<tool_call>
<|im_start|>function=bash_command(command="ls -la .agent/workflows/")
<tool_call>
<|im_start|>function=bash_command(command="cat .agent/workflows/*.md 2>/dev/null || echo 'No markdown files found'")
<tool_call>