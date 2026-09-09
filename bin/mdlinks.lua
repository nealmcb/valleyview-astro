-- Rewrite relative links to .md sources so they point at the built .html
-- pages (leaves absolute http(s) links and non-.md targets alone).
function Link(el)
  local t = el.target
  if t:match("^https?:") then return el end
  el.target = t:gsub("%.md$", ".html"):gsub("%.md#", ".html#")
  return el
end
