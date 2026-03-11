# 推送代码（本地）
cd /Users/ruanlongbo/ai/ai_competion_v2/ai
git add .
git commit -m "描述"
git push

# 部署（远程服务器）
ssh -i /Users/ruanlongbo/ai/deploy/AI_Contest_Key.pem ecs-user@120.77.168.5 "cd /home/ecs-user/ruanlongbo/ai/ai_test && git pull && docker compose up -d --build"