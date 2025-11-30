# Wangumi

## 🧩 后端代码规范

### 1. 代码风格

* 统一使用 Python 官方 PEP8 风格规范。
* 命名规则：函数与变量用小驼峰（`getUserInfo`），类名用大驼峰（`UserProfile`），数据库表名用下划线（`user_profile`）。
* 每个函数写明 docstring（功能、参数、返回值）。

### 2. 提交与分支管理

* **分支命名**

  * `main`：稳定可部署版本
  * `dev`：开发整合分支
  * `feature/<模块名>`：新功能
  * `fix/<问题名>`：修复问题
* **提交信息格式**

  ```
  feat(user): add login API
  fix(auth): correct token refresh
  docs(api): update /user/info doc
  ```
* 每次提交前应本地运行并确认无语法错误。

### 3. 团队协作

* 功能开发 → 创建 feature 分支 → 提交 MR → 代码 Review → 合并。
* 建议每周一次接口同步检查，更新 Apifox 文档。

## 💡 后端设计规范

### 一、接口设计规范

1. **接口风格：RESTful**

   * `/users/` → 获取所有用户
   * `/users/{id}/` → 获取单个用户
   * `POST /users/` → 创建用户
   * `PUT /users/{id}/` → 更新
   * `DELETE /users/{id}/` → 删除

2. **返回格式**

   ```json
   {
     "code": 0,
     "message": "success",
     "data": {...}
   }
   ```

   * `code=0` 表示成功；非0表示错误。
   * 所有错误应返回明确的 `message` 字段。

3. **状态码约定**

   | 状态码 | 含义       |
   | --- | -------- |
   | 200 | 请求成功     |
   | 400 | 请求参数错误   |
   | 401 | 未登录/鉴权失败 |
   | 403 | 权限不足     |
   | 404 | 资源不存在    |
   | 500 | 服务器错误    |

4. **接口文档工具：Apifox**

   * 统一用 Apifox 维护接口定义、调试与 Mock。
   * 每个接口在创建时填写：

     * 请求路径、方法、参数说明
     * 响应样例与字段说明
   * 启用 Mock 数据，便于前端并行开发。
   * 项目地址统一发布到组内。

---

### 二、环境与运行规范

1. **当前阶段**：本地开发为主，无需部署。
2. **必须做的**

   * 固定 Python 与 Django 版本，生成 `requirements.txt`。
---

### 三、协作与测试规范

1. **任务管理**

   * 每个新功能先建立 Issue。
   * 对应建立 `feature/模块名` 分支开发。
   * 功能完成后提交 MR，由reviewer审查后合并。

2. **单元测试建议**

   * 每个模块至少编写关键路径测试（如登录注册、主要数据流）。
   * 由开发该模块的成员负责编写与维护。
   * 测试框架推荐使用 Django 自带的 `unittest` 或 `pytest-django`。

3. **接口自测**

   * 提交前在 Apifox 中验证接口是否正确返回。
   * 确保字段与文档一致。

---

### 四、文档与更新

* 所有规范、接口变更记录于 `/docs` 文件夹。
* README 仅保留简要说明与运行步骤。

## 🔄 周合集同步

* 触发 API：`POST /api/sync/weekly/`（管理员身份），同步完成后返回本次 `SyncLog` 的状态与新增/更新数量。
* 管理命令：在 `backend` 目录执行 `python manage.py sync_weekly`，与 API 共用同一 service 逻辑，可用于 cron/Celery 定时任务。

