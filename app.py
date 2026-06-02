"""
Multi-Website Advertisement Handling System
Backend: Python Flask + SQLite
"""

from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, url_for
import sqlite3
import os
import json
import uuid
import base64
from datetime import datetime, timedelta
import random
import hashlib

app = Flask(__name__)
app.secret_key = 'adms_secret_key_2024'

DB_PATH = 'adms.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS advertisers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT,
            phone TEXT,
            budget REAL DEFAULT 0,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS websites (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT,
            owner TEXT,
            traffic_tier TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'active',
            api_key TEXT UNIQUE,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            advertiser_id TEXT,
            name TEXT NOT NULL,
            description TEXT,
            budget REAL DEFAULT 0,
            spent REAL DEFAULT 0,
            cpm REAL DEFAULT 2.0,
            cpc REAL DEFAULT 0.5,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            targeting TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(advertiser_id) REFERENCES advertisers(id)
        );

        CREATE TABLE IF NOT EXISTS ads (
            id TEXT PRIMARY KEY,
            campaign_id TEXT,
            title TEXT NOT NULL,
            description TEXT,
            ad_type TEXT DEFAULT 'banner',
            size TEXT DEFAULT '728x90',
            image_url TEXT,
            click_url TEXT,
            html_content TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        );

        CREATE TABLE IF NOT EXISTS placements (
            id TEXT PRIMARY KEY,
            website_id TEXT,
            campaign_id TEXT,
            zone TEXT DEFAULT 'header',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(website_id) REFERENCES websites(id),
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        );

        CREATE TABLE IF NOT EXISTS impressions (
            id TEXT PRIMARY KEY,
            ad_id TEXT,
            campaign_id TEXT,
            website_id TEXT,
            ip_hash TEXT,
            user_agent TEXT,
            country TEXT DEFAULT 'IN',
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(ad_id) REFERENCES ads(id)
        );

        CREATE TABLE IF NOT EXISTS clicks (
            id TEXT PRIMARY KEY,
            ad_id TEXT,
            campaign_id TEXT,
            website_id TEXT,
            ip_hash TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(ad_id) REFERENCES ads(id)
        );
    """)
    conn.commit()

    # Seed demo data if empty
    cur.execute("SELECT COUNT(*) FROM advertisers")
    if cur.fetchone()[0] == 0:
        seed_demo_data(conn)

    conn.close()

def seed_demo_data(conn):
    cur = conn.cursor()

    advertisers = [
        ('adv-001', 'Rajan Tech Solutions', 'rajan@techsol.in', 'Tech Solutions Pvt Ltd', '+91-9876543210', 50000),
        ('adv-002', 'Meena Fashion House', 'meena@fashion.in', 'Fashion House', '+91-9876543211', 30000),
        ('adv-003', 'Kumar Electronics', 'kumar@electronics.in', 'Kumar Electronics', '+91-9876543212', 75000),
        ('adv-004', 'Priya Foods', 'priya@foods.in', 'Priya Foods Ltd', '+91-9876543213', 20000),
    ]
    cur.executemany("INSERT OR IGNORE INTO advertisers VALUES (?,?,?,?,?,?,'active',datetime('now'))", advertisers)

    websites = [
        ('web-001', 'Tamil News Today', 'https://tamilnewstoday.in', 'News', 'Admin', 'high', 'active', 'apikey-001'),
        ('web-002', 'Chennai Tech Blog', 'https://chennaitech.blog', 'Technology', 'Admin', 'medium', 'active', 'apikey-002'),
        ('web-003', 'Shopping Deals India', 'https://shoppingdeals.in', 'E-commerce', 'Admin', 'high', 'active', 'apikey-003'),
        ('web-004', 'Food Recipes Tamil', 'https://foodrecipes.in', 'Food', 'Admin', 'low', 'active', 'apikey-004'),
        ('web-005', 'Sports Live Score', 'https://sportslive.in', 'Sports', 'Admin', 'medium', 'active', 'apikey-005'),
    ]
    cur.executemany("INSERT OR IGNORE INTO websites VALUES (?,?,?,?,?,?,?,?,datetime('now'))", websites)

    campaigns = [
        ('camp-001', 'adv-001', 'Tech Product Launch', 'Launch of new software suite', 15000, 4230, 2.5, 0.8, '2025-01-01', '2025-12-31', 'active', '{}'),
        ('camp-002', 'adv-002', 'Summer Fashion Sale', 'Summer collection 50% off', 10000, 3100, 2.0, 0.5, '2025-01-01', '2025-06-30', 'active', '{}'),
        ('camp-003', 'adv-003', 'Electronics Mega Sale', 'Best deals on electronics', 25000, 8900, 3.0, 1.0, '2025-01-01', '2025-12-31', 'active', '{}'),
        ('camp-004', 'adv-004', 'New Food Products', 'Authentic Tamil recipes', 8000, 1200, 1.5, 0.3, '2025-02-01', '2025-08-31', 'active', '{}'),
    ]
    for c in campaigns:
        cur.execute("INSERT OR IGNORE INTO campaigns VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))", c)

    ads = [
        ('ad-001', 'camp-001', 'Tech Software Suite', 'Boost your productivity 10x', 'banner', '728x90', None, 'https://techsol.in', None, 'active'),
        ('ad-002', 'camp-001', 'Free Trial Available', '30-day free trial, no credit card', 'rectangle', '300x250', None, 'https://techsol.in/trial', None, 'active'),
        ('ad-003', 'camp-002', 'Summer Sale 50% Off', 'Shop trending fashion', 'banner', '728x90', None, 'https://fashion.in/sale', None, 'active'),
        ('ad-004', 'camp-003', 'Electronics Best Deals', 'Laptops, Phones & More', 'banner', '728x90', None, 'https://electronics.in', None, 'active'),
        ('ad-005', 'camp-004', 'Authentic Tamil Food', 'Traditional recipes delivered', 'square', '250x250', None, 'https://foods.in', None, 'active'),
    ]
    for a in ads:
        cur.execute("INSERT OR IGNORE INTO ads VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))", a)

    placements = [
        ('pl-001', 'web-001', 'camp-001', 'header', 'active'),
        ('pl-002', 'web-001', 'camp-003', 'sidebar', 'active'),
        ('pl-003', 'web-002', 'camp-001', 'header', 'active'),
        ('pl-004', 'web-003', 'camp-002', 'header', 'active'),
        ('pl-005', 'web-003', 'camp-003', 'footer', 'active'),
        ('pl-006', 'web-004', 'camp-004', 'header', 'active'),
        ('pl-007', 'web-005', 'camp-003', 'sidebar', 'active'),
    ]
    for p in placements:
        cur.execute("INSERT OR IGNORE INTO placements VALUES (?,?,?,?,?,datetime('now'))", p)

    # Generate sample impressions/clicks for past 30 days
    for i in range(500):
        day_offset = random.randint(0, 29)
        ts = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d %H:%M:%S')
        ad_id = random.choice(['ad-001','ad-002','ad-003','ad-004','ad-005'])
        camp_map = {'ad-001':'camp-001','ad-002':'camp-001','ad-003':'camp-002','ad-004':'camp-003','ad-005':'camp-004'}
        web_id = random.choice(['web-001','web-002','web-003','web-004','web-005'])
        imp_id = str(uuid.uuid4())
        cur.execute("INSERT INTO impressions VALUES (?,?,?,?,?,?,?,?)",
            (imp_id, ad_id, camp_map[ad_id], web_id, f'hash{i}', 'Mozilla/5.0', 'IN', ts))

    for i in range(60):
        day_offset = random.randint(0, 29)
        ts = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d %H:%M:%S')
        ad_id = random.choice(['ad-001','ad-002','ad-003','ad-004','ad-005'])
        camp_map = {'ad-001':'camp-001','ad-002':'camp-001','ad-003':'camp-002','ad-004':'camp-003','ad-005':'camp-004'}
        web_id = random.choice(['web-001','web-002','web-003','web-004','web-005'])
        cur.execute("INSERT INTO clicks VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), ad_id, camp_map[ad_id], web_id, f'hash{i}', ts))

    conn.commit()

# ─────────────────────────────────────────────
# FRONTEND ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/advertisers-page')
def advertisers_page():
    return render_template('advertisers.html')

@app.route('/campaigns-page')
def campaigns_page():
    return render_template('campaigns.html')

@app.route('/websites-page')
def websites_page():
    return render_template('websites.html')

@app.route('/ads-page')
def ads_page():
    return render_template('ads.html')

@app.route('/analytics-page')
def analytics_page():
    return render_template('analytics.html')

@app.route('/placements-page')
def placements_page():
    return render_template('placements.html')

# ─────────────────────────────────────────────
# API: DASHBOARD
# ─────────────────────────────────────────────

@app.route('/api/dashboard')
def api_dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM advertisers WHERE status='active'")
    total_advertisers = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM campaigns WHERE status='active'")
    active_campaigns = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM websites WHERE status='active'")
    total_websites = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM impressions WHERE timestamp >= datetime('now', '-30 days')")
    total_impressions = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM clicks WHERE timestamp >= datetime('now', '-30 days')")
    total_clicks = cur.fetchone()[0]

    ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0

    cur.execute("SELECT SUM(spent) FROM campaigns")
    total_revenue = cur.fetchone()[0] or 0

    # Daily impressions last 7 days
    cur.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as count
        FROM impressions
        WHERE timestamp >= datetime('now', '-7 days')
        GROUP BY day ORDER BY day
    """)
    daily_impressions = [{'day': r['day'], 'count': r['count']} for r in cur.fetchall()]

    # Per website impressions
    cur.execute("""
        SELECT w.name, COUNT(i.id) as impressions, COUNT(c.id) as clicks
        FROM websites w
        LEFT JOIN impressions i ON i.website_id = w.id
        LEFT JOIN clicks c ON c.website_id = w.id
        GROUP BY w.id ORDER BY impressions DESC LIMIT 5
    """)
    website_stats = [{'name': r['name'], 'impressions': r['impressions'], 'clicks': r['clicks']} for r in cur.fetchall()]

    # Campaign performance
    cur.execute("""
        SELECT c.name, c.budget, c.spent,
               COUNT(DISTINCT i.id) as impressions,
               COUNT(DISTINCT cl.id) as clicks
        FROM campaigns c
        LEFT JOIN impressions i ON i.campaign_id = c.id
        LEFT JOIN clicks cl ON cl.campaign_id = c.id
        GROUP BY c.id ORDER BY impressions DESC LIMIT 5
    """)
    campaign_perf = [{'name': r['name'], 'budget': r['budget'], 'spent': r['spent'],
                       'impressions': r['impressions'], 'clicks': r['clicks']} for r in cur.fetchall()]

    conn.close()
    return jsonify({
        'total_advertisers': total_advertisers,
        'active_campaigns': active_campaigns,
        'total_websites': total_websites,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'ctr': ctr,
        'total_revenue': round(total_revenue, 2),
        'daily_impressions': daily_impressions,
        'website_stats': website_stats,
        'campaign_performance': campaign_perf
    })

# ─────────────────────────────────────────────
# API: ADVERTISERS
# ─────────────────────────────────────────────

@app.route('/api/advertisers', methods=['GET'])
def get_advertisers():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM advertisers ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/advertisers', methods=['POST'])
def create_advertiser():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    adv_id = 'adv-' + str(uuid.uuid4())[:8]
    try:
        cur.execute("INSERT INTO advertisers VALUES (?,?,?,?,?,?,?,datetime('now'))",
            (adv_id, data['name'], data['email'], data.get('company',''),
             data.get('phone',''), data.get('budget', 0), 'active'))
        conn.commit()
        return jsonify({'success': True, 'id': adv_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/advertisers/<adv_id>', methods=['PUT'])
def update_advertiser(adv_id):
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE advertisers SET name=?, email=?, company=?, phone=?, budget=?, status=? WHERE id=?",
        (data['name'], data['email'], data.get('company',''), data.get('phone',''),
         data.get('budget',0), data.get('status','active'), adv_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/advertisers/<adv_id>', methods=['DELETE'])
def delete_advertiser(adv_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE advertisers SET status='inactive' WHERE id=?", (adv_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# API: WEBSITES
# ─────────────────────────────────────────────

@app.route('/api/websites', methods=['GET'])
def get_websites():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM websites ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/websites', methods=['POST'])
def create_website():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    web_id = 'web-' + str(uuid.uuid4())[:8]
    api_key = 'apikey-' + str(uuid.uuid4())[:16]
    try:
        cur.execute("INSERT INTO websites VALUES (?,?,?,?,?,?,?,?,datetime('now'))",
            (web_id, data['name'], data['url'], data.get('category',''),
             data.get('owner',''), data.get('traffic_tier','medium'), 'active', api_key))
        conn.commit()
        return jsonify({'success': True, 'id': web_id, 'api_key': api_key})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/websites/<web_id>', methods=['PUT'])
def update_website(web_id):
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE websites SET name=?, url=?, category=?, traffic_tier=?, status=? WHERE id=?",
        (data['name'], data['url'], data.get('category',''), data.get('traffic_tier','medium'),
         data.get('status','active'), web_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/websites/<web_id>', methods=['DELETE'])
def delete_website(web_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE websites SET status='inactive' WHERE id=?", (web_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# API: CAMPAIGNS
# ─────────────────────────────────────────────

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, a.name as advertiser_name,
               COUNT(DISTINCT i.id) as impressions,
               COUNT(DISTINCT cl.id) as clicks
        FROM campaigns c
        LEFT JOIN advertisers a ON a.id = c.advertiser_id
        LEFT JOIN impressions i ON i.campaign_id = c.id
        LEFT JOIN clicks cl ON cl.campaign_id = c.id
        GROUP BY c.id ORDER BY c.created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    camp_id = 'camp-' + str(uuid.uuid4())[:8]
    try:
        cur.execute("INSERT INTO campaigns VALUES (?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
            (camp_id, data['advertiser_id'], data['name'], data.get('description',''),
             data.get('budget',0), 0, data.get('cpm',2.0), data.get('cpc',0.5),
             data.get('start_date',''), data.get('end_date',''), 'active',
             json.dumps(data.get('targeting',{}))))
        conn.commit()
        return jsonify({'success': True, 'id': camp_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/campaigns/<camp_id>', methods=['PUT'])
def update_campaign(camp_id):
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE campaigns SET name=?, description=?, budget=?, cpm=?, cpc=?, start_date=?, end_date=?, status=? WHERE id=?",
        (data['name'], data.get('description',''), data.get('budget',0),
         data.get('cpm',2.0), data.get('cpc',0.5), data.get('start_date',''),
         data.get('end_date',''), data.get('status','active'), camp_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/campaigns/<camp_id>', methods=['DELETE'])
def delete_campaign(camp_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE campaigns SET status='paused' WHERE id=?", (camp_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# API: ADS
# ─────────────────────────────────────────────

@app.route('/api/ads', methods=['GET'])
def get_ads():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ads.*, campaigns.name as campaign_name, advertisers.name as advertiser_name,
               COUNT(DISTINCT impressions.id) as impressions,
               COUNT(DISTINCT clicks.id) as clicks
        FROM ads
        LEFT JOIN campaigns ON campaigns.id = ads.campaign_id
        LEFT JOIN advertisers ON advertisers.id = campaigns.advertiser_id
        LEFT JOIN impressions ON impressions.ad_id = ads.id
        LEFT JOIN clicks ON clicks.ad_id = ads.id
        GROUP BY ads.id ORDER BY ads.created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/ads', methods=['POST'])
def create_ad():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    ad_id = 'ad-' + str(uuid.uuid4())[:8]
    try:
        cur.execute("INSERT INTO ads VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'))",
            (ad_id, data['campaign_id'], data['title'], data.get('description',''),
             data.get('ad_type','banner'), data.get('size','728x90'),
             data.get('image_url',''), data.get('click_url',''),
             data.get('html_content',''), 'active'))
        conn.commit()
        return jsonify({'success': True, 'id': ad_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/ads/<ad_id>', methods=['DELETE'])
def delete_ad(ad_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE ads SET status='inactive' WHERE id=?", (ad_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# API: PLACEMENTS
# ─────────────────────────────────────────────

@app.route('/api/placements', methods=['GET'])
def get_placements():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, w.name as website_name, w.url as website_url,
               c.name as campaign_name, a.name as advertiser_name
        FROM placements p
        LEFT JOIN websites w ON w.id = p.website_id
        LEFT JOIN campaigns c ON c.id = p.campaign_id
        LEFT JOIN advertisers a ON a.id = c.advertiser_id
        ORDER BY p.created_at DESC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

@app.route('/api/placements', methods=['POST'])
def create_placement():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    pl_id = 'pl-' + str(uuid.uuid4())[:8]
    try:
        cur.execute("INSERT INTO placements VALUES (?,?,?,?,?,datetime('now'))",
            (pl_id, data['website_id'], data['campaign_id'],
             data.get('zone','header'), 'active'))
        conn.commit()
        return jsonify({'success': True, 'id': pl_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        conn.close()

@app.route('/api/placements/<pl_id>', methods=['DELETE'])
def delete_placement(pl_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE placements SET status='inactive' WHERE id=?", (pl_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ─────────────────────────────────────────────
# API: AD SERVING (for websites to use)
# ─────────────────────────────────────────────

@app.route('/api/serve/<website_id>/<zone>')
def serve_ad(website_id, zone):
    """Ad serving endpoint - websites call this to get ads"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT ads.id, ads.title, ads.description, ads.ad_type, ads.size,
               ads.image_url, ads.click_url, ads.html_content,
               campaigns.id as campaign_id
        FROM placements
        JOIN campaigns ON campaigns.id = placements.campaign_id
        JOIN ads ON ads.campaign_id = campaigns.id
        WHERE placements.website_id = ? AND placements.zone = ?
          AND placements.status = 'active'
          AND campaigns.status = 'active'
          AND ads.status = 'active'
        ORDER BY RANDOM() LIMIT 1
    """, (website_id, zone))

    ad = cur.fetchone()
    if not ad:
        conn.close()
        return jsonify({'error': 'No ad available'}), 404

    ad = dict(ad)

    # Record impression
    imp_id = str(uuid.uuid4())
    ip_hash = hashlib.md5(request.remote_addr.encode()).hexdigest()
    cur.execute("INSERT INTO impressions VALUES (?,?,?,?,?,?,?,datetime('now'))",
        (imp_id, ad['id'], ad['campaign_id'], website_id, ip_hash,
         request.headers.get('User-Agent',''), 'IN'))
    conn.commit()
    conn.close()

    return jsonify({
        'ad_id': ad['id'],
        'title': ad['title'],
        'description': ad['description'],
        'type': ad['ad_type'],
        'size': ad['size'],
        'image_url': ad['image_url'],
        'click_url': f"/api/click/{ad['id']}/{website_id}",
        'html_content': ad['html_content']
    })

@app.route('/api/click/<ad_id>/<website_id>')
def track_click(ad_id, website_id):
    """Track click and redirect"""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT campaign_id, click_url FROM ads WHERE id=?", (ad_id,))
    ad = cur.fetchone()

    if ad:
        ip_hash = hashlib.md5(request.remote_addr.encode()).hexdigest()
        cur.execute("INSERT INTO clicks VALUES (?,?,?,?,?,datetime('now'))",
            (str(uuid.uuid4()), ad_id, ad['campaign_id'], website_id, ip_hash))
        conn.commit()
        redirect_url = ad['click_url'] or '/'
    else:
        redirect_url = '/'

    conn.close()
    return redirect(redirect_url)

# ─────────────────────────────────────────────
# API: ANALYTICS
# ─────────────────────────────────────────────

@app.route('/api/analytics')
def get_analytics():
    days = int(request.args.get('days', 30))
    conn = get_db()
    cur = conn.cursor()

    # Daily stats
    cur.execute("""
        SELECT DATE(timestamp) as day,
               COUNT(*) as impressions
        FROM impressions
        WHERE timestamp >= datetime('now', ? || ' days')
        GROUP BY day ORDER BY day
    """, (f'-{days}',))
    daily_imp = {r['day']: r['impressions'] for r in cur.fetchall()}

    cur.execute("""
        SELECT DATE(timestamp) as day, COUNT(*) as clicks
        FROM clicks
        WHERE timestamp >= datetime('now', ? || ' days')
        GROUP BY day ORDER BY day
    """, (f'-{days}',))
    daily_clicks = {r['day']: r['clicks'] for r in cur.fetchall()}

    # Merge daily data
    all_days = sorted(set(list(daily_imp.keys()) + list(daily_clicks.keys())))
    daily_data = [{'day': d, 'impressions': daily_imp.get(d,0), 'clicks': daily_clicks.get(d,0)} for d in all_days]

    # By website
    cur.execute("""
        SELECT w.name, COUNT(DISTINCT i.id) as impressions, COUNT(DISTINCT c.id) as clicks
        FROM websites w
        LEFT JOIN impressions i ON i.website_id = w.id AND i.timestamp >= datetime('now', ? || ' days')
        LEFT JOIN clicks c ON c.website_id = w.id AND c.timestamp >= datetime('now', ? || ' days')
        GROUP BY w.id ORDER BY impressions DESC
    """, (f'-{days}', f'-{days}'))
    by_website = [dict(r) for r in cur.fetchall()]

    # By campaign
    cur.execute("""
        SELECT c.name, COUNT(DISTINCT i.id) as impressions, COUNT(DISTINCT cl.id) as clicks, c.budget, c.spent
        FROM campaigns c
        LEFT JOIN impressions i ON i.campaign_id = c.id AND i.timestamp >= datetime('now', ? || ' days')
        LEFT JOIN clicks cl ON cl.campaign_id = c.id AND cl.timestamp >= datetime('now', ? || ' days')
        GROUP BY c.id ORDER BY impressions DESC
    """, (f'-{days}', f'-{days}'))
    by_campaign = [dict(r) for r in cur.fetchall()]

    # Totals
    cur.execute("SELECT COUNT(*) FROM impressions WHERE timestamp >= datetime('now', ? || ' days')", (f'-{days}',))
    total_impressions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM clicks WHERE timestamp >= datetime('now', ? || ' days')", (f'-{days}',))
    total_clicks = cur.fetchone()[0]

    conn.close()
    return jsonify({
        'daily': daily_data,
        'by_website': by_website,
        'by_campaign': by_campaign,
        'total_impressions': total_impressions,
        'total_clicks': total_clicks,
        'ctr': round(total_clicks/total_impressions*100, 2) if total_impressions else 0
    })

# ─────────────────────────────────────────────
# STATIC FILES
# ─────────────────────────────────────────────

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("  Multi-Website Ad Management System")
    print("  Running at: http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
