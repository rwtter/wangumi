# Wangumi Android 壳工程

Kotlin + Jetpack Compose 初始化框架，直接对接 Django `api/`。

## 使用

```bash
cd frontend_app
./gradlew assembleDebug
```

若需自定义后端地址，在 `local.properties` 中增加：

```
django.backendUrl=http://10.0.2.2:8000/api/
```
