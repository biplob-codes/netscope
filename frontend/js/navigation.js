const Navigation = (() => {
  const titles = {
    dashboard: "Dashboard",
    live: "Live Monitor",
    history: "Usage History",
    insights: "Insights",
    reports: "Reports",
    interfaces: "Interfaces",
    quota: "Data Limits",
    settings: "Settings",
  };

  let current = "dashboard";
  const loaders = {};

  function register(page, loaderFn) {
    loaders[page] = loaderFn;
  }

  function go(page) {
    if (!titles[page]) return;
    current = page;

    document.querySelectorAll(".nav-item").forEach((el) => {
      el.classList.toggle("active", el.dataset.page === page);
    });
    document.querySelectorAll(".page").forEach((el) => {
      el.classList.toggle("active", el.id === `page-${page}`);
    });
    document.getElementById("page-title").textContent = titles[page];

    if (loaders[page]) {
      loaders[page]();
    }
  }

  function init() {
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => go(btn.dataset.page));
    });
  }

  return { init, go, register, get current() { return current; } };
})();
