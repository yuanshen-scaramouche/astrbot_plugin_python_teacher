# Python 学习教练（python_teacher）

一个用于帮助用户系统学习 Python 的 AstrBot 插件，内置学习路线、课程推进、练习与测验，并可接入 OpenAI 兼容接口进行 AI 答疑与个性化讲解。

## 安装

将本插件目录复制到 AstrBot 的 `data/plugins/` 下，然后重启/重载 AstrBot。

## 使用方法

### 指令

- `/py 路线`：查看系统学习路线（模块列表）
- `/py 开始`：初始化学习进度
- `/py 状态`：查看当前学习进度
- `/py 模块 <模块名或编号>`：查看某模块的课程列表
- `/py 课 <课编号>`：进入某一课（讲解 + 示例）
- `/py 下` / `/py next`：进入下一课
- `/py 上` / `/py prev`：进入上一课
- `/py 练习`：生成与当前课匹配的练习题
- `/py 答案 <你的答案/数量>`：提交练习答案（文字）或指定使用最后 n 个文件（1-5，默认1）；支持上传多个文件（.py/.txt/.md/.ipynb/.json/.yaml/.csv 等）
- `/py 测验`：对当前模块进行小测
- `/py 配置`：显示当前 AI 配置（隐藏 key）

### AI 答疑

- `/py 问 <问题>`：向 AI 提问（会结合你的当前进度与本课知识点）
- `/py 问 <文件数量> <问题>`：先上传文件（支持常见代码/文本格式：py/js/c/cpp/html/css/go/java/php/toml/json/yaml/sql/rb/rs 等），再提问，AI 会同时看到文件内容与问题
- `/py 清空记忆`：清空 AI 的对话历史记忆

## 配置项

配置通过 `_conf_schema.json` 定义（在 AstrBot 的插件配置面板里填写）：

| 配置项 | 说明 | 默认值 |
|------|------|------|
| api_base | OpenAI 兼容接口 base URL | http://localhost:8000/v1 |
| api_key | API Key | mock-key |
| model | 模型名称 | mock-model |
| system_profile | 教学风格系统提示词 | 见默认值 |
| max_turns | 单次对话最大追问轮数 | 6 |

## 更新日志

见 [CHANGELOG.md](./CHANGELOG.md)

## 联系方式（如果有问题或建议，欢迎联系。）
- 邮箱：510160951@qq.com
- 加群：[1042904301](https://a.aa.cab/a/qun.php/1042904301)
- QQ号：510160951

## 致谢

- [AstrBot](https://github.com/Soulter/AstrBot) - 一个强大的多平台机器人框架
- [Trae](https://trae.ai) - AI 开发助手，让开发更高效
- [GPT](https://openai.com/) - 提供强大的语言模型能力
