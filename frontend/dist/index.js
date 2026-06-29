(function() {
  var r = window.QwenPaw;
  if (!r || !r.host || !r.host.React) return;
  var m = r.host.React, t = m.createElement, a = m.useState, R = m.useEffect, S = "/plugin/jie-browser", v = "jie-browser";
  function j() {
    var [e, p] = a("control"), [u, T] = a({ plugins_count: 0, tools_count: 0, version: "", screen: {} }), [_, h] = a(!0), [c, d] = a(""), [k, A] = a(100), [C, E] = a(100), [w, I] = a("Hello"), g = r.host, B = async function() {
      h(!0);
      try {
        var l = await g.fetch(g.getApiUrl("/jie-browser/stats")), s = await l.json();
        var platformDisplay = s.platform;
        if (!platformDisplay || platformDisplay === "unknown") {
          platformDisplay = s.has_windows_api ? "Windows" : (s.has_linux_tools ? "Linux" : "unknown");
        }
        T({
          plugins_count: s.plugins_count || 0,
          tools_count: s.tools_count || 0,
          version: s.version || "unknown",
          platform: platformDisplay,
          screen: s.screen || {}
        }), d("系统状态加载成功");
      } catch (b) {
        d("加载失败: " + b.message);
      }
      h(!1);
    };
    R(function() {
      B();
    }, []);
    var o = async function(l, s) {
      try {
        d("执行中...");
        var b = await g.fetch(g.getApiUrl("/jie-browser/" + l), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(s)
        }), O = await b.json();
        return d(l + " 成功"), O;
      } catch (L) {
        d(l + " 失败: " + L.message);
      }
    }, y = { padding: "10px 20px", margin: "0 5px", borderRadius: "6px", cursor: "pointer", border: "none", background: "#333", color: "#fff" }, f = { padding: "10px 20px", margin: "0 5px", borderRadius: "6px", cursor: "pointer", border: "none", background: "#667eea", color: "#fff" }, n = { padding: "8px 16px", margin: "5px", borderRadius: "4px", cursor: "pointer", border: "1px solid #555", background: "#222", color: "#fff" }, x = { padding: "8px", margin: "5px", borderRadius: "4px", border: "1px solid #555", background: "#111", color: "#fff", width: "100px" }, i = { background: "#252540", padding: "15px", borderRadius: "8px", margin: "10px 0", border: "1px solid #3a3a5e" };
    return t(
      "div",
      { style: { padding: "20px", color: "#fff", fontFamily: "sans-serif", background: "#1a1a2e", minHeight: "100vh" } },
      t(
        "h1",
        { style: { marginBottom: "20px", display: "flex", alignItems: "center", gap: "10px" } },
        "🖥️",
        t("span", null, "界 AI浏览器"),
        t("span", { style: { fontSize: "14px", color: "#888", marginLeft: "10px" } }, "v" + u.version),
        t("span", { style: { fontSize: "12px", color: "#667eea", marginLeft: "10px", padding: "2px 8px", background: "#252540", borderRadius: "4px" } }, u.platform || "检测中")
      ),
      // 标签页
      t(
        "div",
        { style: { marginBottom: "20px", display: "flex", borderBottom: "1px solid #333", paddingBottom: "10px" } },
        t("button", { style: e === "control" ? f : y, onClick: function() {
          p("control");
        } }, "🎮 控制台"),
        t("button", { style: e === "snapshot" ? f : y, onClick: function() {
          p("snapshot");
        } }, "📸 截图"),
        t("button", { style: e === "click" ? f : y, onClick: function() {
          p("click");
        } }, "🖱️ 点击"),
        t("button", { style: e === "type" ? f : y, onClick: function() {
          p("type");
        } }, "⌨️ 输入"),
        t("button", { style: e === "tools" ? f : y, onClick: function() {
          p("tools");
        } }, "🛠️ 工具")
      ),
      // 控制台标签
      e === "control" && t(
        "div",
        null,
        t(
          "div",
          { style: i },
          t("h3", { style: { marginBottom: "10px" } }, "📊 系统状态"),
          _ ? t("p", null, "加载中...") : t(
            "div",
            null,
            t("p", null, t("strong", null, "插件数量: "), u.plugins_count),
            t("p", null, t("strong", null, "工具数量: "), u.tools_count),
            t("p", null, t("strong", null, "屏幕分辨率: "), (u.screen.width || 0) + "x" + (u.screen.height || 0)),
            t("p", { style: { color: "#4caf50", marginTop: "10px" } }, c)
          ),
          t("button", { style: n, onClick: B }, "🔄 刷新")
        ),
        t(
          "div",
          { style: i },
          t("h3", { style: { marginBottom: "10px" } }, "🚀 快速操作"),
          t(
            "div",
            null,
            t("button", { style: n, onClick: function() {
              o("snapshot", {});
            } }, "📸 截图"),
            t("button", { style: n, onClick: function() {
              o("app", { name: "notepad" });
            } }, "📝 记事本"),
            t("button", { style: n, onClick: function() {
              o("app", { name: "calc" });
            } }, "🧮 计算器"),
            t("button", { style: n, onClick: function() {
              o("app", { name: "msedge" });
            } }, "🌐 Edge浏览器")
          )
        )
      ),
      // 截图标签
      e === "snapshot" && t(
        "div",
        { style: i },
        t("h3", { style: { marginBottom: "10px" } }, "📸 屏幕截图"),
        t("p", { style: { color: "#aaa", marginBottom: "10px" } }, "点击按钮截取当前屏幕"),
        t("button", { style: n, onClick: function() {
          o("snapshot", {});
        } }, "📸 执行截图"),
        t("p", { style: { marginTop: "10px", color: c.includes("成功") ? "#4caf50" : "#ff9800" } }, c)
      ),
      // 点击标签
      e === "click" && t(
        "div",
        { style: i },
        t("h3", { style: { marginBottom: "10px" } }, "🖱️ 鼠标点击"),
        t(
          "div",
          { style: { marginBottom: "10px" } },
          t("label", { style: { marginRight: "5px" } }, "X坐标:"),
          t("input", { type: "number", value: k, style: x, onChange: function(l) {
            A(parseInt(l.target.value) || 0);
          } }),
          t("label", { style: { margin: "0 5px" } }, "Y坐标:"),
          t("input", { type: "number", value: C, style: x, onChange: function(l) {
            E(parseInt(l.target.value) || 0);
          } })
        ),
        t("button", { style: n, onClick: function() {
          o("click", { x: k, y: C });
        } }, "🖱️ 点击指定坐标"),
        t("p", { style: { marginTop: "10px", color: "#aaa" } }, c)
      ),
      // 输入标签
      e === "type" && t(
        "div",
        { style: i },
        t("h3", { style: { marginBottom: "10px" } }, "⌨️ 键盘输入"),
        t(
          "div",
          { style: { marginBottom: "10px" } },
          t("input", { type: "text", value: w, style: { ...x, width: "300px" }, onChange: function(l) {
            I(l.target.value);
          } })
        ),
        t(
          "div",
          null,
          t("button", { style: n, onClick: function() {
            o("type", { text: w });
          } }, "⌨️ 输入文字"),
          t("button", { style: n, onClick: function() {
            o("shortcut", { keys: "ctrl+a" });
          } }, "Ctrl+A"),
          t("button", { style: n, onClick: function() {
            o("shortcut", { keys: "ctrl+c" });
          } }, "Ctrl+C"),
          t("button", { style: n, onClick: function() {
            o("shortcut", { keys: "ctrl+v" });
          } }, "Ctrl+V"),
          t("button", { style: n, onClick: function() {
            o("shortcut", { keys: "enter" });
          } }, "Enter")
        ),
        t("p", { style: { marginTop: "10px", color: "#aaa" } }, c)
      ),
      // 工具标签
      e === "tools" && t(
        "div",
        null,
        t(
          "div",
          { style: i },
          t("h3", { style: { marginBottom: "10px" } }, "🛠️ 系统工具"),
          t(
            "div",
            null,
            t("button", { style: n, onClick: function() {
              o("windows", {});
            } }, "🪟 窗口列表"),
            t("button", { style: n, onClick: function() {
              o("cursor", {});
            } }, "🖱️ 鼠标位置"),
            t("button", { style: n, onClick: function() {
              o("stats", {});
            } }, "📊 刷新状态")
          )
        ),
        t(
          "div",
          { style: i },
          t("h3", { style: { marginBottom: "10px" } }, "⏺️ 录制回放"),
          t(
            "div",
            null,
            t("button", { style: n, onClick: function() {
              o("record/start", { name: "测试录制" });
            } }, "⏺️ 开始录制"),
            t("button", { style: n, onClick: function() {
              o("record/stop", {});
            } }, "⏹️ 停止录制"),
            t("button", { style: n, onClick: function() {
              o("records", {});
            } }, "📋 录制列表")
          )
        ),
        t(
          "div",
          { style: i },
          t("h3", { style: { marginBottom: "10px" } }, "🔍 OCR识别"),
          t(
            "div",
            null,
            t("button", { style: n, onClick: function() {
              o("ocr", {});
            } }, "🔍 屏幕OCR识别")
          )
        ),
        t("p", { style: { marginTop: "10px", color: c.includes("成功") ? "#4caf50" : "#ff9800" } }, c)
      )
    );
  }
  if (r.route && r.route.add)
    try {
      r.route.add(v, [{ id: "jie-browser.home", path: S, component: function() {
        return t(j);
      } }]);
    } catch (e) {
      console.log("route.add err:", e);
    }
  if (r.menu && r.menu.add)
    try {
      r.menu.add(v, [{ id: "jie-browser-main", location: "primary.settings", label: "界", icon: function() {
        return t("span", { style: { fontSize: "18px" } }, "🖥️");
      }, route: "jie-browser.home", order: 30 }]);
    } catch (e) {
      console.log("menu.add err:", e);
    }
})();
