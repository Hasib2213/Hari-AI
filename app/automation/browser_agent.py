from playwright.async_api import async_playwright

class BrowserAgent:
    async def analyze(self,url):
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            page=await browser.new_page()
            await page.goto(url,wait_until="domcontentloaded",timeout=30000)
            fields=await page.locator("input,textarea,select").evaluate_all("""
            els => els.map((el,i) => {
              let label="";
              if(el.id){const l=document.querySelector(`label[for="${el.id}"]`); if(l) label=l.innerText.trim();}
              label=label || el.getAttribute("aria-label") || el.placeholder || el.name || "";
              return {
                selector: el.id ? "#"+el.id : "",
                field_type: el.tagName.toLowerCase()==="select" ? "select" : (el.type||el.tagName.toLowerCase()),
                label, name: el.name||"", required: !!el.required,
                options: el.tagName.toLowerCase()==="select" ? [...el.options].map(x=>x.textContent.trim()) : []
              };
            })
            """)
            title=await page.title()
            await browser.close()
            return {"url":url,"title":title,"fields":fields}

    async def fill(self,url,mappings,dry_run=True):
        filled=[]; skipped=[]; missing=[]
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            page=await browser.new_page()
            await page.goto(url,wait_until="domcontentloaded",timeout=30000)
            for m in mappings:
                try:
                    if m["value_source"] in {"skip","user_required"}:
                        skipped.append(m["field_label"])
                        continue
                    loc=page.locator(m["selector"]).first if m["selector"] else page.get_by_label(m["field_label"]).first
                    if not await loc.count():
                        skipped.append(m["field_label"]); continue
                    if dry_run:
                        filled.append(m["field_label"]); continue
                    typ=await loc.get_attribute("type")
                    tag=await loc.evaluate("(e)=>e.tagName.toLowerCase()")
                    if typ=="file":
                        skipped.append(m["field_label"])
                    elif tag=="select":
                        await loc.select_option(label=m["value"])
                        filled.append(m["field_label"])
                    elif typ in {"checkbox","radio"}:
                        if str(m["value"]).lower() in {"true","yes","1","on"}:
                            await loc.check()
                        filled.append(m["field_label"])
                    else:
                        await loc.fill(str(m["value"]))
                        filled.append(m["field_label"])
                except Exception:
                    skipped.append(m["field_label"])
            await browser.close()
        return {"filled":filled,"skipped":skipped,"missing_required":missing,"dry_run":dry_run}

    async def submit(self,url,dry_run=True):
        if dry_run: return {"submitted":False,"reason":"dry_run"}
        async with async_playwright() as p:
            browser=await p.chromium.launch(headless=True)
            page=await browser.new_page()
            await page.goto(url,wait_until="domcontentloaded",timeout=30000)
            button=page.locator('button[type="submit"],input[type="submit"]').first
            await button.click(timeout=10000)
            await page.wait_for_load_state("domcontentloaded")
            result={"submitted":True,"final_url":page.url,"title":await page.title()}
            await browser.close()
            return result
