const fs = require('fs');
const path = require('path');
const vm = require('vm');

const WORKFLOW_DIR = path.join(__dirname);
const WORKFLOW_FILES = [
  '01_daily_social_insights_sync.json',
  '02_content_performance_tracker.json',
  '03_ondemand_sync_webhook.json',
  '04_meta_token_keeper.json'
];

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, message) {
  totalTests++;
  if (condition) {
    passedTests++;
    console.log(`  ✅ PASS: ${message}`);
  } else {
    failedTests++;
    console.error(`  ❌ FAIL: ${message}`);
  }
}

// Luxon-like mock for $now
function createMockNow(baseDate = new Date('2026-09-07T12:00:00Z')) {
  return {
    _d: new Date(baseDate),
    minus({ days = 0, hours = 0 } = {}) {
      const d = new Date(this._d);
      d.setDate(d.getDate() - days);
      d.setHours(d.getHours() - hours);
      return createMockNow(d);
    },
    plus({ days = 0, hours = 0 } = {}) {
      const d = new Date(this._d);
      d.setDate(d.getDate() + days);
      d.setHours(d.getHours() + hours);
      return createMockNow(d);
    },
    startOf(unit) {
      const d = new Date(this._d);
      if (unit === 'day') {
        d.setUTCHours(0, 0, 0, 0);
      }
      return createMockNow(d);
    },
    endOf(unit) {
      const d = new Date(this._d);
      if (unit === 'day') {
        d.setUTCHours(23, 59, 59, 999);
      }
      return createMockNow(d);
    },
    toSeconds() {
      return Math.floor(this._d.getTime() / 1000);
    },
    toFormat(fmt) {
      if (fmt === 'yyyy-MM-dd') {
        return this._d.toISOString().slice(0, 10);
      }
      return this._d.toISOString();
    },
    toISO() {
      return this._d.toISOString();
    }
  };
}

console.log('\n======================================================');
console.log('--- STARTING N8N WORKFLOW VALIDATION & SIMULATION ---');
console.log('======================================================\n');

for (const filename of WORKFLOW_FILES) {
  const filePath = path.join(WORKFLOW_DIR, filename);
  console.log(`\n📁 Inspecting Workflow: ${filename}`);

  // 1. File exists and valid JSON
  let content;
  try {
    content = fs.readFileSync(filePath, 'utf8');
    assert(true, `${filename} read successfully`);
  } catch (err) {
    assert(false, `Could not read ${filename}: ${err.message}`);
    continue;
  }

  let workflow;
  try {
    workflow = JSON.parse(content);
    assert(true, `${filename} is valid JSON`);
  } catch (err) {
    assert(false, `${filename} failed JSON parsing: ${err.message}`);
    continue;
  }

  // 2. Structural checks
  assert(typeof workflow.name === 'string' && workflow.name.length > 0, `Workflow has valid name: "${workflow.name}"`);
  assert(Array.isArray(workflow.nodes) && workflow.nodes.length > 0, `Workflow contains ${workflow.nodes.length} nodes`);
  assert(typeof workflow.connections === 'object', `Workflow contains connections map`);

  const nodeNames = new Set(workflow.nodes.map(n => n.name));
  assert(nodeNames.size === workflow.nodes.length, `All ${workflow.nodes.length} node names are unique`);

  // Check each node
  for (const node of workflow.nodes) {
    assert(typeof node.id === 'string' && node.id.length > 0, `Node "${node.name}" has id: ${node.id}`);
    assert(typeof node.type === 'string' && node.type.startsWith('n8n-nodes-base.'), `Node "${node.name}" has valid n8n type: ${node.type}`);
    assert(typeof node.typeVersion === 'number', `Node "${node.name}" has typeVersion: ${node.typeVersion}`);
    assert(Array.isArray(node.position) && node.position.length === 2, `Node "${node.name}" has valid canvas coordinates`);
  }

  // Check connections integrity
  for (const [sourceNode, connectionData] of Object.entries(workflow.connections)) {
    assert(nodeNames.has(sourceNode), `Connection source "${sourceNode}" exists in nodes list`);
    if (connectionData.main) {
      for (const outputList of connectionData.main) {
        if (Array.isArray(outputList)) {
          for (const target of outputList) {
            assert(nodeNames.has(target.node), `Connection target "${target.node}" exists in nodes list`);
          }
        }
      }
    }
  }
}

// 2b. SPECIFIC TOPOLOGY CHECKS (Break & Fix validation)
console.log('\n======================================================');
console.log('--- TOPOLOGY & EXECUTION ENGINE SAFETY CHECKS ---');
console.log('======================================================\n');

// Verify Workflow 1 has no fan-in race condition
const wf1Json = JSON.parse(fs.readFileSync(path.join(WORKFLOW_DIR, '01_daily_social_insights_sync.json'), 'utf8'));
const inDegreeWf1 = {};
for (const [src, data] of Object.entries(wf1Json.connections)) {
  for (const outList of data.main || []) {
    for (const target of outList) {
      inDegreeWf1[target.node] = (inDegreeWf1[target.node] || 0) + 1;
    }
  }
}
const maxInDegreeWf1 = Math.max(...Object.values(inDegreeWf1));
assert(maxInDegreeWf1 === 1, `Workflow 1 is strictly linear (max incoming connections = ${maxInDegreeWf1}), preventing fan-in duplicate execution`);

// Verify Workflow 3 has no fan-in race condition (prevents 'Response already sent' crash)
const wf3Json = JSON.parse(fs.readFileSync(path.join(WORKFLOW_DIR, '03_ondemand_sync_webhook.json'), 'utf8'));
const inDegreeWf3 = {};
for (const [src, data] of Object.entries(wf3Json.connections)) {
  for (const outList of data.main || []) {
    for (const target of outList) {
      inDegreeWf3[target.node] = (inDegreeWf3[target.node] || 0) + 1;
    }
  }
}
const maxInDegreeWf3 = Math.max(...Object.values(inDegreeWf3));
assert(maxInDegreeWf3 === 1, `Workflow 3 is strictly linear (max incoming connections = ${maxInDegreeWf3}), preventing duplicate webhook responses`);

// Verify Workflow 4 connects to Send Critical Alert to Webhook
const wf4Json = JSON.parse(fs.readFileSync(path.join(WORKFLOW_DIR, '04_meta_token_keeper.json'), 'utf8'));
const hasAlertHttpNode = wf4Json.nodes.some(n => n.name === 'Send Critical Alert to Webhook');
assert(hasAlertHttpNode, 'Workflow 4 contains HTTP node to dispatch critical token alerts');
const alertConns = wf4Json.connections['Prepare Critical Token Alert'];
const alertDispatched = alertConns?.main?.[0]?.some(t => t.node === 'Send Critical Alert to Webhook');
assert(alertDispatched, 'Workflow 4 properly connects "Prepare Critical Token Alert" to "Send Critical Alert to Webhook"');


// 3. CODE NODE LOGIC SIMULATION & TESTS
console.log('\n======================================================');
console.log('--- TESTING CODE NODE LOGIC WITH REAL-WORLD SIMULATION ---');
console.log('======================================================\n');

// Test Workflow 1 Code Nodes
console.log('🧪 Testing Workflow 1 (Daily Profile & Account Sync) Logic...');
const initNode1 = wf1Json.nodes.find(n => n.name === 'Init Config & Calculate Dates');
const initContext1 = {
  $now: createMockNow(new Date('2026-09-07T01:00:00Z')),
  $env: {
    META_ACCESS_TOKEN: 'TEST_TOKEN_XYZ',
    META_IG_USER_ID: '17841400000000000',
    META_FB_PAGE_ID: '100000000000000',
    DENTALPIN_API_BASE_URL: 'https://dental-api-2z19.onrender.com',
    DENTALPIN_API_KEY: 'test-key-123'
  }
};
const initResult1 = vm.runInNewContext(`(function() { ${initNode1.parameters.jsCode} })()`, initContext1);
assert(Array.isArray(initResult1) && initResult1.length === 1, 'Init node returns 1 item array');
assert(initResult1[0].json.target_date === '2026-09-06', `Target date calculated correctly as yesterday (${initResult1[0].json.target_date})`);
assert(initResult1[0].json.meta_access_token === 'TEST_TOKEN_XYZ', 'Meta access token resolved from environment');
assert(initResult1[0].json.dentalpin_api_base === 'https://dental-api-2z19.onrender.com', 'DentalPin base URL resolved');
assert(initResult1[0].json.dentalpin_sync_url.includes('/social_automation/insights'), 'DentalPin sync URL generated');

// Normalize & Build Unified Insights
const normNode1 = wf1Json.nodes.find(n => n.name === 'Normalize & Build Unified Insights');

// Scenario 1: Healthy normal data from Meta Graph API
const normContextHealthy = {
  $now: createMockNow(),
  $: (nodeName) => {
    if (nodeName === 'Init Config & Calculate Dates') {
      return { first: () => initResult1[0] };
    }
    if (nodeName === 'Fetch Instagram Profile') {
      return { first: () => ({ json: { followers_count: 3580, username: 'dr_mokhtar_dental' } }) };
    }
    if (nodeName === 'Fetch Instagram Insights') {
      return {
        first: () => ({
          json: {
            data: [
              { name: 'reach', values: [{ value: 2450 }] },
              { name: 'profile_views', values: [{ value: 142 }] },
              { name: 'website_clicks', values: [{ value: 38 }] }
            ]
          }
        })
      };
    }
    if (nodeName === 'Fetch Facebook Page Info') {
      return { first: () => ({ json: { followers_count: 4890, name: 'Dr Mokhtar Cabinet' } }) };
    }
    if (nodeName === 'Fetch Facebook Page Insights') {
      return {
        first: () => ({
          json: {
            data: [
              { name: 'page_impressions_unique', values: [{ value: 1890 }] },
              { name: 'page_views_total', values: [{ value: 95 }] },
              { name: 'page_total_actions', values: [{ value: 42 }] }
            ]
          }
        })
      };
    }
    return { first: () => ({ json: {} }) };
  }
};
const normResultHealthy = vm.runInNewContext(`(function() { ${normNode1.parameters.jsCode} })()`, normContextHealthy);
assert(Array.isArray(normResultHealthy) && normResultHealthy.length === 1, 'Normalize returns 1 result item');
const payloadHealthy = normResultHealthy[0].json.sync_payload;
assert(Array.isArray(payloadHealthy.insights) && payloadHealthy.insights.length === 2, 'Sync payload has 2 insight records');
assert(payloadHealthy.insights[0].platform === 'instagram' && payloadHealthy.insights[0].total_followers === 3580, 'Instagram followers matched 3580');
assert(payloadHealthy.insights[0].reach === 2450 && payloadHealthy.insights[0].profile_views === 142, 'Instagram reach and views matched');
assert(payloadHealthy.insights[1].platform === 'facebook' && payloadHealthy.insights[1].total_followers === 4890, 'Facebook followers matched 4890');
assert(payloadHealthy.insights[1].reach === 1890 && payloadHealthy.insights[1].website_clicks === 42, 'Facebook reach and actions matched');

// Scenario 2: Empty insights data (new account or Meta delay)
const normContextEmpty = {
  $now: createMockNow(),
  $: (nodeName) => {
    if (nodeName === 'Init Config & Calculate Dates') return { first: () => initResult1[0] };
    if (nodeName === 'Fetch Instagram Profile') return { first: () => ({ json: { followers_count: 0 } }) };
    if (nodeName === 'Fetch Instagram Insights') return { first: () => ({ json: { data: [] } }) };
    if (nodeName === 'Fetch Facebook Page Info') return { first: () => ({ json: { fan_count: 0 } }) };
    if (nodeName === 'Fetch Facebook Page Insights') return { first: () => ({ json: { data: [] } }) };
    return { first: () => ({ json: {} }) };
  }
};
const normResultEmpty = vm.runInNewContext(`(function() { ${normNode1.parameters.jsCode} })()`, normContextEmpty);
assert(normResultEmpty[0].json.sync_payload.insights[0].reach === 0, 'Gracefully handles empty IG insights without crash');
assert(normResultEmpty[0].json.sync_payload.insights[1].reach === 0, 'Gracefully handles empty FB insights without crash');

// Scenario 3: Meta API error returned
const normContextError = {
  $now: createMockNow(),
  $: (nodeName) => {
    if (nodeName === 'Init Config & Calculate Dates') return { first: () => initResult1[0] };
    if (nodeName === 'Fetch Instagram Profile') return { first: () => ({ json: { error: { message: 'Rate limit reached', code: 4 } } }) };
    if (nodeName === 'Fetch Instagram Insights') return { first: () => ({ json: { error: { message: 'Rate limit reached', code: 4 } } }) };
    if (nodeName === 'Fetch Facebook Page Info') return { first: () => ({ json: { error: { message: 'Rate limit reached', code: 4 } } }) };
    if (nodeName === 'Fetch Facebook Page Insights') return { first: () => ({ json: { error: { message: 'Rate limit reached', code: 4 } } }) };
    return { first: () => ({ json: {} }) };
  }
};
const normResultError = vm.runInNewContext(`(function() { ${normNode1.parameters.jsCode} })()`, normContextError);
assert(normResultError[0].json.sync_payload.insights[0].total_followers === 0, 'Gracefully handles Meta API error objects without crash');


// Test Workflow 2 Code Nodes
console.log('\n🧪 Testing Workflow 2 (Reels & Content Performance Tracker) Logic...');
const wf2Json = JSON.parse(fs.readFileSync(path.join(WORKFLOW_DIR, '02_content_performance_tracker.json'), 'utf8'));
const filterNode2 = wf2Json.nodes.find(n => n.name === 'Filter Media & Set Adaptive Metrics');

const mediaPayloadMixed = {
  data: [
    {
      id: 'media_101',
      caption: 'Cas clinique: Pose dimplant sans douleur #implantdentaire',
      media_type: 'VIDEO',
      media_product_type: 'REELS',
      timestamp: '2026-09-06T15:00:00+0000',
      like_count: 85,
      comments_count: 14
    },
    {
      id: 'media_102',
      caption: 'Avant / Après blanchiment dentaire au fauteuil',
      media_type: 'IMAGE',
      media_product_type: 'POST',
      timestamp: '2026-09-06T11:00:00+0000',
      like_count: 142,
      comments_count: 22
    }
  ]
};
const filterContextMixed = {
  $json: mediaPayloadMixed,
  $: () => ({ first: () => ({ json: { target_date: '2026-09-06', ig_account_id: 'dr_mokhtar_dental', meta_access_token: 'TOKEN' } }) })
};
const filterResultMixed = vm.runInNewContext(`(function() { ${filterNode2.parameters.jsCode} })()`, filterContextMixed);
assert(filterResultMixed.length === 2, 'Filtered 2 media items');
assert(filterResultMixed[0].json.metric_query.includes('plays'), 'VIDEO item contains plays in metric_query');
assert(!filterResultMixed[1].json.metric_query.includes('plays'), 'IMAGE item does NOT contain plays (prevents Meta error 100)');

const filterContextEmpty = {
  $json: { data: [] },
  $: () => ({ first: () => ({ json: { target_date: '2026-09-06', ig_account_id: 'dr_mokhtar_dental', meta_access_token: 'TOKEN' } }) })
};
const filterResultEmpty = vm.runInNewContext(`(function() { ${filterNode2.parameters.jsCode} })()`, filterContextEmpty);
assert(filterResultEmpty.length === 1 && filterResultEmpty[0].json.is_empty === true, 'Empty media list flagged is_empty = true without crashing');

const aggNode2 = wf2Json.nodes.find(n => n.name === 'Aggregate Content & Daily Saves');
const aggContext = {
  $: (name) => {
    if (name === 'Init Config & Settings') return { first: () => ({ json: { target_date: '2026-09-06', ig_account_id: 'dr_mokhtar_dental' } }) };
    if (name === 'Filter Media & Set Adaptive Metrics') {
      return {
        all: () => filterResultMixed
      };
    }
    if (name === 'Fetch Media Insights') {
      return {
        all: () => [
          { json: { data: [{ name: 'saved', values: [{ value: 34 }] }, { name: 'plays', values: [{ value: 1250 }] }] } },
          { json: { data: [{ name: 'saved', values: [{ value: 18 }] }] } }
        ]
      };
    }
  }
};
const aggResult = vm.runInNewContext(`(function() { ${aggNode2.parameters.jsCode} })()`, aggContext);
assert(aggResult[0].json.sync_payload.saves === 52, `Total aggregated saves: ${aggResult[0].json.sync_payload.saves} (34 + 18 = 52)`);
assert(aggResult[0].json.stats.total_plays === 1250, 'Total video reel plays aggregated correctly');


// Test Workflow 3 Code Nodes
console.log('\n🧪 Testing Workflow 3 (On-Demand Social Insights Sync Webhook) Logic...');
const parseNode3 = wf3Json.nodes.find(n => n.name === 'Parse Doctor Request & Date');
const parseContext3 = {
  $json: { body: { requested_by: 'Dr. Mokhtar', date: '2026-09-07' } },
  $now: createMockNow(),
  $env: { META_ACCESS_TOKEN: 'TOKEN_123', DENTALPIN_API_BASE_URL: 'https://dental-api-2z19.onrender.com' }
};
const parseResult3 = vm.runInNewContext(`(function() { ${parseNode3.parameters.jsCode} })()`, parseContext3);
assert(parseResult3[0].json.requested_by === 'Dr. Mokhtar', 'Doctor name correctly parsed from webhook');
assert(parseResult3[0].json.target_date === '2026-09-07', 'Doctor target date correctly parsed');


// Test Workflow 4 Code Nodes
console.log('\n🧪 Testing Workflow 4 (Meta Token Keeper) Logic...');
const analyzeNode4 = wf4Json.nodes.find(n => n.name === 'Analyze Token Health & Expiration');

// Scenario 1: Healthy Token (45 days remaining)
const contextHealthyToken = {
  $now: createMockNow(),
  $json: {
    data: {
      is_valid: true,
      expires_at: Math.floor(Date.now() / 1000) + (45 * 86400),
      scopes: ['pages_show_list', 'instagram_basic', 'instagram_manage_insights'],
      type: 'USER'
    }
  },
  $: () => ({ first: () => ({ json: { meta_access_token: 'TOK', meta_app_id: 'APP1', meta_app_secret: 'SEC1' } }) })
};
const resHealthyToken = vm.runInNewContext(`(function() { ${analyzeNode4.parameters.jsCode} })()`, contextHealthyToken);
assert(resHealthyToken[0].json.status === 'HEALTHY', 'Status is HEALTHY for 45 days remaining');
assert(resHealthyToken[0].json.needs_refresh === false, 'needs_refresh is false for healthy token');

// Scenario 2: Token expiring soon (4 days remaining)
const contextExpiringToken = {
  $now: createMockNow(),
  $json: {
    data: {
      is_valid: true,
      expires_at: Math.floor(Date.now() / 1000) + (4 * 86400),
      scopes: ['pages_show_list', 'instagram_basic'],
      type: 'USER'
    }
  },
  $: () => ({ first: () => ({ json: { meta_access_token: 'TOK', meta_app_id: 'APP1', meta_app_secret: 'SEC1' } }) })
};
const resExpiringToken = vm.runInNewContext(`(function() { ${analyzeNode4.parameters.jsCode} })()`, contextExpiringToken);
assert(resExpiringToken[0].json.status === 'EXPIRING_SOON', 'Status is EXPIRING_SOON when <= 7 days left');
assert(resExpiringToken[0].json.needs_refresh === true, 'needs_refresh is true when <= 7 days left');

// Scenario 3: Permanent Page Access Token (expires_at === 0)
const contextPermanentToken = {
  $now: createMockNow(),
  $json: {
    data: {
      is_valid: true,
      expires_at: 0,
      scopes: ['pages_show_list', 'instagram_basic'],
      type: 'PAGE'
    }
  },
  $: () => ({ first: () => ({ json: { meta_access_token: 'TOK', meta_app_id: 'APP1', meta_app_secret: 'SEC1' } }) })
};
const resPermanentToken = vm.runInNewContext(`(function() { ${analyzeNode4.parameters.jsCode} })()`, contextPermanentToken);
assert(resPermanentToken[0].json.status === 'PERMANENT_HEALTHY', 'Status is PERMANENT_HEALTHY for expires_at === 0');
assert(resPermanentToken[0].json.is_permanent === true, 'is_permanent is true for Page tokens');

// Scenario 4: Invalid/Revoked Token
const contextInvalidToken = {
  $now: createMockNow(),
  $json: {
    data: {
      is_valid: false,
      error: { message: 'Session has expired' }
    }
  },
  $: () => ({ first: () => ({ json: { meta_access_token: 'TOK', meta_app_id: 'APP1', meta_app_secret: 'SEC1' } }) })
};
const resInvalidToken = vm.runInNewContext(`(function() { ${analyzeNode4.parameters.jsCode} })()`, contextInvalidToken);
assert(resInvalidToken[0].json.status === 'INVALID_OR_REVOKED', 'Status is INVALID_OR_REVOKED for invalid token');
assert(resInvalidToken[0].json.is_critical === true, 'is_critical is true for revoked token');

// Scenario 5: Evaluate Refresh Result - SUCCESS
const evalNode4 = wf4Json.nodes.find(n => n.name === 'Evaluate Refresh Result');
const contextRefreshSuccess = {
  $now: createMockNow(),
  $json: {
    access_token: 'NEW_EXTENDED_LONG_LIVED_TOKEN_XYZ',
    token_type: 'bearer',
    expires_in: 5184000
  },
  $: (name) => {
    if (name === 'Analyze Token Health & Expiration') {
      return {
        first: () => ({
          json: {
            status: 'EXPIRING_SOON',
            days_remaining: 4,
            expiry_date: '2026-09-11 12:00:00 UTC',
            app_id: '12345',
            scopes: ['pages_show_list'],
            alert_webhook_url: 'https://dental-api-2z19.onrender.com/api/v1/notifications'
          }
        })
      };
    }
  }
};
const resRefreshSuccess = vm.runInNewContext(`(function() { ${evalNode4.parameters.jsCode} })()`, contextRefreshSuccess);
assert(resRefreshSuccess[0].json.refresh_success === true, 'Evaluate Refresh Result flags success when access_token received');
assert(resRefreshSuccess[0].json.days_remaining === 60, 'Days remaining updated to 60 days on successful refresh');
assert(resRefreshSuccess[0].json.is_critical === false, 'is_critical is false on successful refresh');

// Scenario 6: Evaluate Refresh Result - FAILURE (triggers alert!)
const contextRefreshFailure = {
  $now: createMockNow(),
  $json: {
    error: {
      message: 'Error validating verification code. Please authorize again.',
      type: 'OAuthException',
      code: 100
    }
  },
  $: (name) => {
    if (name === 'Analyze Token Health & Expiration') {
      return {
        first: () => ({
          json: {
            status: 'EXPIRING_SOON',
            days_remaining: 2,
            expiry_date: '2026-09-09 12:00:00 UTC',
            app_id: '12345',
            scopes: ['pages_show_list'],
            alert_webhook_url: 'https://dental-api-2z19.onrender.com/api/v1/notifications'
          }
        })
      };
    }
  }
};
const resRefreshFailure = vm.runInNewContext(`(function() { ${evalNode4.parameters.jsCode} })()`, contextRefreshFailure);
assert(resRefreshFailure[0].json.refresh_success === false, 'Evaluate Refresh Result flags failure when Meta rejects exchange');
assert(resRefreshFailure[0].json.is_critical === true, 'is_critical is TRUE on refresh failure to route to alert');

// Scenario 7: Prepare Critical Token Alert
const prepAlertNode4 = wf4Json.nodes.find(n => n.name === 'Prepare Critical Token Alert');
const contextPrepAlert = {
  $now: createMockNow(),
  $: (name) => {
    if (name === 'Analyze Token Health & Expiration') {
      return {
        first: () => ({
          json: {
            status: 'EXPIRING_SOON',
            days_remaining: 2,
            expiry_date: '2026-09-09 12:00:00 UTC',
            app_id: '12345',
            scopes: ['pages_show_list'],
            alert_webhook_url: 'https://dental-api-2z19.onrender.com/api/v1/notifications'
          }
        })
      };
    }
    if (name === 'Evaluate Refresh Result') {
      return {
        first: () => resRefreshFailure[0]
      };
    }
  }
};
const resPrepAlert = vm.runInNewContext(`(function() { ${prepAlertNode4.parameters.jsCode} })()`, contextPrepAlert);
assert(resPrepAlert[0].json.severity === 'CRITICAL', 'Alert severity is CRITICAL');
assert(resPrepAlert[0].json.alert_webhook_url === 'https://dental-api-2z19.onrender.com/api/v1/notifications', 'Alert webhook target URL preserved');
assert(resPrepAlert[0].json.message.includes('échoué'), 'Alert message details refresh failure in French for clinic team');


console.log('\n======================================================');
console.log(`--- TEST RESULTS: ${passedTests}/${totalTests} PASSED, ${failedTests} FAILED ---`);
console.log('======================================================\n');

if (failedTests > 0) {
  process.exit(1);
} else {
  console.log('🎉 ALL WORKFLOW VALIDATIONS AND SIMULATION TESTS PASSED!\n');
}
