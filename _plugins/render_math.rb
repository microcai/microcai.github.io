# 构建完成后把公式渲染成 MathML，让产物成为不需要 JavaScript 的纯静态页面。
# 注意：GitHub Pages 自带的 Jekyll 构建会忽略 _plugins，所以本站改用 GitHub Actions 构建。
require "open3"

Jekyll::Hooks.register :site, :post_write do |site|
  script = File.join(site.source, "tools", "render-math.js")
  next unless File.exist?(script)

  stdout, stderr, status = Open3.capture3("node", script, site.dest)
  if status.success?
    Jekyll.logger.info "MathML:", stdout.strip
  else
    Jekyll.logger.warn "MathML:", "渲染失败，公式会保留 LaTeX 原文"
    Jekyll.logger.warn "MathML:", stderr.strip
  end
end
