const { createApp } = Vue;

const FALLBACK_COVER = "https://dummyimage.com/400x600/f5f5f5/e0e0e0&text=No+Cover";

createApp({
  data() {
    return {
      searchQuery: "",
      apiStatus: {
        message: "API 状态：检查中...",
        isError: false,
      },
      isLoading: true,
      sections: [],
      trending: [],
      boardPosts: [],
      rawAnime: [],
      loginForm: {
        username: "",
        password: "",
        loading: false,
        error: "",
        success: "",
        tokens: null,
      },
      registerForm: {
        username: "",
        email: "",
        cellphone: "",
        code: "",
        password: "",
        loading: false,
        sending: false,
        error: "",
        success: "",
      },
    };
  },
  computed: {
    currentYear() {
      return new Date().getFullYear();
    },
  },
  mounted() {
    this.fetchHealth();
    this.fetchAnime();
  },
  methods: {
    buildApiUrl(path) {
      const base = ((window.API_BASE_URL && window.API_BASE_URL.trim()) || "/api").replace(/\/+$/, "");
      if (!path.startsWith("/")) {
        return `${base}/${path}`;
      }
      return `${base}${path}`;
    },
    async fetchHealth() {
      try {
        const response = await fetch(this.buildApiUrl("/health"));
        const data = await response.json();
        const statusText = data && data.status ? data.status : "正常";
        this.apiStatus = { message: `API 状态：${statusText}`, isError: false };
      } catch (error) {
        this.apiStatus = { message: `API 状态：${error.message}`, isError: true };
      }
    },
    async fetchAnime() {
      this.isLoading = true;
      try {
        const response = await fetch(this.buildApiUrl("/anime?limit=60&sort=热度"));
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const payload = await response.json();
        if (!payload || payload.code !== 0 || !payload.data) {
          throw new Error(payload?.message || "数据加载失败");
        }
        const list = Array.isArray(payload.data.list) ? payload.data.list : [];
        this.rawAnime = list.map((item) => this.decorateAnime(item));
        this.sections = this.buildSections(this.rawAnime);
        this.trending = this.buildTrending(this.rawAnime);
        this.boardPosts = this.buildBoardPosts(this.rawAnime);
      } catch (error) {
        this.sections = [];
        console.error(error);
        this.apiStatus = { message: `API 状态：${error.message}`, isError: true };
      } finally {
        this.isLoading = false;
      }
    },
    decorateAnime(item) {
      const rating = typeof item.rating === "number" ? item.rating : 0;
      const popularity = typeof item.popularity === "number" ? item.popularity : 0;
      const summary = (item.summary || "暂无简介").toString().replace(/\s+/g, " ");
      return {
        ...item,
        rating: rating ? rating.toFixed(1) : "暂无",
        popularity,
        summary: summary.length > 58 ? `${summary.slice(0, 58)}…` : summary,
        cover: item.cover || FALLBACK_COVER,
        category: Array.isArray(item.category) ? item.category : [],
      };
    },
    buildSections(list) {
      const groups = new Map();
      list.forEach((item) => {
        const fallbackName = "未分类";
        const categories = item.category.length ? item.category : [fallbackName];
        const key = categories[0];
        if (!groups.has(key)) {
          groups.set(key, []);
        }
        const bucket = groups.get(key);
        if (bucket.length < 8) {
          bucket.push(item);
        }
      });
      return Array.from(groups.entries())
        .sort((a, b) => b[1].length - a[1].length)
        .slice(0, 6)
        .map(([name, items]) => ({ name, items }));
    },
    buildTrending(list) {
      const sorted = [...list]
        .sort((a, b) => (parseFloat(b.rating) || 0) - (parseFloat(a.rating) || 0) || b.popularity - a.popularity)
        .slice(0, 6)
        .map((item, index) => ({
          id: item.id,
          title: item.title,
          rating: item.rating,
          popularity: item.popularity,
          rank: index + 1,
        }));
      return sorted;
    },
    buildBoardPosts(list) {
      return list.slice(0, 6).map((item) => {
        const date = item.time ? new Date(item.time).toLocaleDateString() : "刚刚";
        return {
          title: `社区热议：《${item.title}》`,
          date,
        };
      });
    },
    quickSearch() {
      const term = this.searchQuery.trim();
      if (!term) {
        this.sections = this.buildSections(this.rawAnime);
        return;
      }
      const lowered = term.toLowerCase();
      const filtered = this.rawAnime.filter((item) => item.title.toLowerCase().includes(lowered));
      this.sections = filtered.length ? this.buildSections(filtered) : [];
    },
    scrollToLogin() {
      const el = this.$refs.loginPanel;
      if (el && el.scrollIntoView) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    },
    scrollToRegister() {
      const el = this.$refs.registerPanel;
      if (el && el.scrollIntoView) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    },
    async submitLogin() {
      if (!this.loginForm.username || !this.loginForm.password) {
        this.loginForm.error = "请输入用户名和密码";
        return;
      }
      this.loginForm.loading = true;
      this.loginForm.error = "";
      this.loginForm.success = "";
      this.loginForm.tokens = null;
      try {
        const response = await fetch(this.buildApiUrl("/login/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: this.loginForm.username,
            password: this.loginForm.password,
          }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.detail || data?.message || "登录失败");
        }
        this.loginForm.success = "登录成功！请妥善保存 Access / Refresh Token。";
        this.loginForm.tokens = data;
      } catch (error) {
        this.loginForm.error = error.message;
      } finally {
        this.loginForm.loading = false;
      }
    },
    async sendVerification() {
      if (!this.registerForm.email && !this.registerForm.cellphone) {
        this.registerForm.error = "请填写邮箱或手机号以接收验证码";
        return;
      }
      this.registerForm.error = "";
      this.registerForm.success = "";
      this.registerForm.sending = true;
      try {
        const payload = {};
        if (this.registerForm.email) {
          payload.email = this.registerForm.email;
        }
        if (this.registerForm.cellphone) {
          payload.cellphone = this.registerForm.cellphone;
        }
        const response = await fetch(this.buildApiUrl("/send_verification_code/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.error || data?.message || "验证码发送失败");
        }
        this.registerForm.success = "验证码已发送，请查收";
      } catch (error) {
        this.registerForm.error = error.message;
      } finally {
        this.registerForm.sending = false;
      }
    },
    formatTokens(tokens) {
      try {
        return JSON.stringify(tokens, null, 2);
      } catch (error) {
        return String(tokens);
      }
    },
    async submitRegister() {
      const form = this.registerForm;
      if (!form.username || !form.password || !form.code || (!form.email && !form.cellphone)) {
        form.error = "请完整填写注册信息并输入验证码";
        return;
      }
      form.loading = true;
      form.error = "";
      form.success = "";
      try {
        const response = await fetch(this.buildApiUrl("/register/"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            username: form.username,
            password: form.password,
            email: form.email,
            cellphone: form.cellphone,
            code: form.code,
          }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data?.error || data?.message || "注册失败");
        }
        form.success = data?.message || "注册成功，欢迎加入 Wangumi！";
        form.username = "";
        form.email = "";
        form.cellphone = "";
        form.code = "";
        form.password = "";
      } catch (error) {
        form.error = error.message;
      } finally {
        form.loading = false;
      }
    },
  },
}).mount("#app");
