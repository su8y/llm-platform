module.exports = {
    apps: [
        {
            name: "mcp-server",
            cwd: "/home/ec2-user/llm-platform/staging/mcp-agent-server",
            script: "run_server.sh",
            interpreter: "bash",
            exec_mode: "fork",
            autorestart: true,
            watch: false,
            merge_logs: true,
            out_file: "/home/ec2-user/.pm2/logs/mcp-server-out.log",
            error_file: "/home/ec2-user/.pm2/logs/mcp-server-error.log",
            env: {
                VIRTUAL_ENV: "/home/ec2-user/llm-platform/staging/mcp-agent-server/venv",
                PATH: "/home/ec2-user/llm-platform/staging/mcp-agent-server/.venv/bin:/home/ec2-user/.local/bin:/home/ec2-user/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin"
            }
        }
    ]
};
