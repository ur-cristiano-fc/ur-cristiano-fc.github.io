#!/usr/bin/env python3
"""Utility script to manage used topics tracking"""
import json
import os
from datetime import datetime, timedelta
import argparse


USED_TOPICS_FILE = "_posts/used_topics.json"


def load_topics():
    """Load used topics from file"""
    if not os.path.exists(USED_TOPICS_FILE):
        return {}
    
    with open(USED_TOPICS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_topics(topics):
    """Save topics to file"""
    os.makedirs(os.path.dirname(USED_TOPICS_FILE) or '.', exist_ok=True)
    with open(USED_TOPICS_FILE, 'w', encoding='utf-8') as f:
        json.dump(topics, f, indent=2, ensure_ascii=False)


def list_topics(topics):
    """List all used topics"""
    if not topics:
        print("📋 No used topics found")
        return
    
    print(f"\n📋 Used Topics ({len(topics)}):")
    print("=" * 80)
    
    # Sort by date
    sorted_topics = sorted(
        topics.items(),
        key=lambda x: x[1].get('date', ''),
        reverse=True
    )
    
    for i, (key, data) in enumerate(sorted_topics, 1):
        title = data.get('title', key)
        date = data.get('date', 'Unknown')
        permalink = data.get('permalink', 'N/A')
        
        # Parse date for display
        try:
            dt = datetime.fromisoformat(date)
            date_str = dt.strftime('%Y-%m-%d %H:%M')
            age_days = (datetime.now() - dt).days
            age_str = f"({age_days}d ago)"
        except:
            date_str = date
            age_str = ""
        
        print(f"\n{i}. {title[:70]}")
        print(f"   Permalink: {permalink}")
        print(f"   Date: {date_str} {age_str}")


def clean_old_topics(topics, days=30):
    """Remove topics older than specified days"""
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.isoformat()
    
    original_count = len(topics)
    topics = {
        k: v for k, v in topics.items()
        if v.get('date', '') > cutoff_str
    }
    removed = original_count - len(topics)
    
    print(f"🧹 Cleaned {removed} topics older than {days} days")
    print(f"📊 Remaining topics: {len(topics)}")
    
    return topics


def clear_all_topics():
    """Clear all used topics"""
    confirm = input("⚠️  Are you sure you want to clear ALL used topics? (yes/no): ")
    if confirm.lower() == 'yes':
        if os.path.exists(USED_TOPICS_FILE):
            os.remove(USED_TOPICS_FILE)
        print("✅ All topics cleared!")
    else:
        print("❌ Cancelled")


def remove_topic(topics, search_term):
    """Remove a specific topic by search term"""
    search_lower = search_term.lower()
    matches = []
    
    for key, data in topics.items():
        title = data.get('title', key).lower()
        if search_lower in title or search_lower in key:
            matches.append((key, data))
    
    if not matches:
        print(f"❌ No topics found matching: {search_term}")
        return topics
    
    if len(matches) == 1:
        key, data = matches[0]
        print(f"📍 Found: {data.get('title', key)}")
        confirm = input("Remove this topic? (yes/no): ")
        if confirm.lower() == 'yes':
            del topics[key]
            print("✅ Topic removed!")
        else:
            print("❌ Cancelled")
    else:
        print(f"\n📍 Found {len(matches)} matching topics:")
        for i, (key, data) in enumerate(matches, 1):
            print(f"{i}. {data.get('title', key)[:60]}")
        
        try:
            choice = int(input("\nEnter number to remove (0 to cancel): "))
            if choice == 0:
                print("❌ Cancelled")
            elif 1 <= choice <= len(matches):
                key, data = matches[choice - 1]
                del topics[key]
                print(f"✅ Removed: {data.get('title', key)[:60]}")
            else:
                print("❌ Invalid choice")
        except ValueError:
            print("❌ Invalid input")
    
    return topics


def stats(topics):
    """Show statistics about used topics"""
    if not topics:
        print("📊 No topics to analyze")
        return
    
    print(f"\n📊 Statistics:")
    print("=" * 80)
    print(f"Total topics: {len(topics)}")
    
    # Count by age
    now = datetime.now()
    age_buckets = {
        'Last 24h': 0,
        'Last 7d': 0,
        'Last 30d': 0,
        'Older': 0
    }
    
    for data in topics.values():
        try:
            date = datetime.fromisoformat(data.get('date', ''))
            age = (now - date).days
            
            if age < 1:
                age_buckets['Last 24h'] += 1
            elif age < 7:
                age_buckets['Last 7d'] += 1
            elif age < 30:
                age_buckets['Last 30d'] += 1
            else:
                age_buckets['Older'] += 1
        except:
            age_buckets['Older'] += 1
    
    for label, count in age_buckets.items():
        print(f"  {label}: {count}")
    
    # Show oldest and newest
    dates = []
    for data in topics.values():
        try:
            dates.append(datetime.fromisoformat(data.get('date', '')))
        except:
            pass
    
    if dates:
        oldest = min(dates)
        newest = max(dates)
        print(f"\n  Oldest: {oldest.strftime('%Y-%m-%d')}")
        print(f"  Newest: {newest.strftime('%Y-%m-%d')}")


def main():
    parser = argparse.ArgumentParser(
        description='Manage used topics for blog generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all used topics
  %(prog)s clean                   # Remove topics older than 30 days
  %(prog)s clean --days 7          # Remove topics older than 7 days
  %(prog)s remove "ronaldo 960"    # Remove specific topic
  %(prog)s clear                   # Clear all topics
  %(prog)s stats                   # Show statistics
        """
    )
    
    parser.add_argument(
        'action',
        choices=['list', 'clean', 'clear', 'remove', 'stats'],
        help='Action to perform'
    )
    parser.add_argument(
        'search_term',
        nargs='?',
        help='Search term for remove action'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days for clean action (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Load topics
    topics = load_topics()
    
    # Perform action
    if args.action == 'list':
        list_topics(topics)
    
    elif args.action == 'clean':
        topics = clean_old_topics(topics, args.days)
        save_topics(topics)
    
    elif args.action == 'clear':
        clear_all_topics()
    
    elif args.action == 'remove':
        if not args.search_term:
            print("❌ Error: search_term required for remove action")
            print("Usage: manage_topics.py remove 'search term'")
            return
        topics = remove_topic(topics, args.search_term)
        save_topics(topics)
    
    elif args.action == 'stats':
        stats(topics)


if __name__ == "__main__":
    main()