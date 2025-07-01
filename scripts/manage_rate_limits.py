#!/usr/bin/env python3
# scripts/manage_rate_limits.py

import asyncio
import sys
import argparse
from typing import Optional

# Add src to path for imports
sys.path.append('src')

from api.middleware.rate_limiter import set_user_tier, get_user_tier, get_rate_limit_stats, RateLimitConfig


async def list_tiers():
    """List available tiers and their limits."""
    print("Available Rate Limit Tiers:")
    print("-" * 40)
    for tier, limit in RateLimitConfig.RATE_LIMITS.items():
        print(f"{tier:10} : {limit:5} requests/day")
    print()


async def set_tier(user_id: str, tier: str):
    """Set user tier."""
    if tier not in RateLimitConfig.RATE_LIMITS:
        print(f"Error: Invalid tier '{tier}'")
        await list_tiers()
        return False
    
    success = await set_user_tier(user_id, tier)
    if success:
        limit = RateLimitConfig.RATE_LIMITS[tier]
        print(f"✓ Set user '{user_id}' to '{tier}' tier ({limit} requests/day)")
        return True
    else:
        print(f"✗ Failed to set user tier for '{user_id}'")
        return False


async def get_tier(user_id: str):
    """Get user tier."""
    tier = await get_user_tier(user_id)
    limit = RateLimitConfig.RATE_LIMITS[tier]
    print(f"User '{user_id}' is in '{tier}' tier ({limit} requests/day)")


async def show_stats():
    """Show rate limiting statistics."""
    stats = await get_rate_limit_stats()
    
    if "error" in stats:
        print(f"Error getting stats: {stats['error']}")
        return
    
    print("Rate Limiting Statistics:")
    print("-" * 40)
    print(f"Total requests:     {stats.get('total_requests', 0)}")
    print(f"Blocked requests:   {stats.get('blocked_requests', 0)}")
    print(f"Block rate:         {stats.get('block_rate', 0):.2%}")
    print(f"Uptime:            {stats.get('uptime_hours', 0):.2f} hours")
    print()
    
    print("Requests by tier:")
    for tier, count in stats.get('requests_by_tier', {}).items():
        print(f"  {tier}: {count}")
    print()
    
    print("Blocked by tier:")
    for tier, count in stats.get('blocked_by_tier', {}).items():
        print(f"  {tier}: {count}")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Manage rate limiting for Football News DB")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List tiers command
    subparsers.add_parser('list-tiers', help='List available tiers')
    
    # Set tier command
    set_parser = subparsers.add_parser('set-tier', help='Set user tier')
    set_parser.add_argument('user_id', help='User ID')
    set_parser.add_argument('tier', help='Tier name (free, premium, admin)')
    
    # Get tier command
    get_parser = subparsers.add_parser('get-tier', help='Get user tier')
    get_parser.add_argument('user_id', help='User ID')
    
    # Stats command
    subparsers.add_parser('stats', help='Show rate limiting statistics')
    
    # Batch set command
    batch_parser = subparsers.add_parser('batch-set', help='Set multiple users to same tier')
    batch_parser.add_argument('tier', help='Tier name')
    batch_parser.add_argument('user_ids', nargs='+', help='User IDs')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'list-tiers':
            await list_tiers()
        
        elif args.command == 'set-tier':
            await set_tier(args.user_id, args.tier)
        
        elif args.command == 'get-tier':
            await get_tier(args.user_id)
        
        elif args.command == 'stats':
            await show_stats()
        
        elif args.command == 'batch-set':
            print(f"Setting {len(args.user_ids)} users to '{args.tier}' tier...")
            success_count = 0
            for user_id in args.user_ids:
                if await set_tier(user_id, args.tier):
                    success_count += 1
            print(f"✓ Successfully set {success_count}/{len(args.user_ids)} users")
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 