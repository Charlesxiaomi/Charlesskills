# wechat-cli 安装与排错

## 安装

```bash
npm install -g @canghe_ai/wechat-cli   # 推荐，需要 Node.js
pip install wechat-cli                 # 备选，需要 Python 3.10+
```

## 初始化（提取密钥，必做）

前提：微信正在运行且已登录。

```bash
sudo wechat-cli init      # macOS / Linux（需要 sudo 扫描内存）
wechat-cli init           # Windows：必须用管理员权限的终端
```

若本地登录过多个微信号，会让你选一个，默认第一个。

## 适配的微信版本

实测可用：**Windows 4.1.9.57 / macOS 4.1.0.34**。装好后关掉微信自动更新——升级后大概率因版本不兼容失效，届时需按新版本号重装对应的微信和 CLI。

- Windows 4.1.9.57: https://github.com/cscnk52/wechat-windows-versions/releases/download/v4.1.9.57/weixin_4.1.9.57.exe
- macOS 4.1.0.34: https://github.com/canc3s/wechat-versions/releases/download/v4.1.0.34-mac_20250929/WeChatMac-4.1.0.34.dmg

## 常见故障

| 症状 | 排查 |
| --- | --- |
| init 失败 | ① 微信在运行且已登录？② 版本对不对？③ macOS 终端有没有「完全磁盘访问权限」？④ Windows 是否管理员终端？ |
| 读不到数据目录（macOS） | 系统设置 → 隐私与安全性 → 完全磁盘访问权限，加入所用终端（Terminal / iTerm2 / IDE 终端），**重启终端** |
| `task_for_pid failed` | macOS 安全限制。让工具自动重签名微信 → **完全退出**微信（非最小化）→ 重新打开并登录 → 再跑 `sudo wechat-cli init`。重签名不会封号，但会影响微信自动更新 |
| 之前能用突然不行 | 多半是微信自动更新了，回到上面的适配版本 |
| 查询返回空 | 名字没匹配上，先 `sessions` / `contacts --query` 拿准确名字 |

## 安全边界

只读本地数据库文件，不发消息、不改数据、不模拟操作，不联网、不上传，不会封号。仅用于查询用户自己的本地微信数据。
