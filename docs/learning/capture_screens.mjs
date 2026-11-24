// Capture public aggregates and the authored demo; retain original PNG bytes.
import {chromium} from '../../frontend/node_modules/playwright-core/index.mjs'
import {writeFile} from 'node:fs/promises'
const browser=await chromium.launch({headless:true,...(process.env.MAILSENSE_BROWSER ? {executablePath:process.env.MAILSENSE_BROWSER} : {})})
try {
 const page=await browser.newPage({viewport:{width:1366,height:900},reducedMotion:'reduce'})
 const routes=['/','/dataset','/probability','/statistics','/detect','/evaluation']
 for(const route of routes){
  await page.goto('http://localhost:5173'+route)
  await page.locator('main h1').waitFor()
  await page.getByText('Local API ready',{exact:true}).waitFor()
  if(route==='/'||route==='/dataset')await page.getByText('5,862',{exact:true}).first().waitFor()
  if(route==='/dataset')await page.getByText('Top 15 words · 5,862 emails',{exact:true}).waitFor()
  if(route==='/probability')await page.getByText('Empirical probabilities · count / denominator',{exact:true}).waitFor()
  if(route==='/statistics'){
   await page.getByRole('button',{name:'Run chi-square test'}).click()
   await page.getByText('Pearson test · no Yates continuity correction',{exact:true}).waitFor()
   await page.getByText('Two-sided Wilson score bounds',{exact:true}).waitFor()
  }
  if(route==='/detect'){
   await page.getByRole('button',{name:'Load synthetic example'}).click()
   await page.getByRole('button',{name:'Classify with both models'}).click()
   await page.locator('.model-result').first().waitFor()
  }
  if(route==='/evaluation')await page.getByText('Measured model metrics · positive class spam',{exact:true}).waitFor()
  await page.evaluate(()=>window.scrollTo(0,0));await page.waitForTimeout(150)
  await page.screenshot({path:'docs/learning/figures/'+(route.slice(1)||'overview')+'.png',fullPage:true})
 }
 await writeFile('docs/learning/screenshots.json',JSON.stringify({captured_at:new Date().toISOString(),browser:browser.version(),viewport:'1366x900',routes,result:'pass',content:'Public aggregates and explicitly authored synthetic meeting text only; production preview.'},null,2)+'\n')
 console.log('Six production tutorial screens captured with real readiness/results; no private message records.')
} finally {await browser.close()}
