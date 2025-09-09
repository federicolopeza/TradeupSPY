#!/usr/bin/env python3
"""
CS2 Items Game Float Caps ETL Pipeline
Parses Valve KeyValues file to extract paint kit float caps and enrich CSFloat catalogs.
"""

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Prefer proven VDF parser if available; fallback to minimal parser otherwise
try:
    import vdf  # type: ignore
    HAS_VDF = True
except Exception:  # pragma: no cover - optional dependency
    vdf = None  # type: ignore
    HAS_VDF = False


class KeyValuesParser:
    """Robust KeyValues (VDF) parser for Valve data files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse KeyValues content into a nested dictionary."""
        if HAS_VDF:
            try:
                return vdf.loads(content)  # type: ignore[attr-defined]
            except Exception as e:
                self.logger.warning("vdf.loads() failed, falling back to minimal parser: %s", e)
        lines = content.split('\n')
        return self._parse_block(lines, 0)[0]
    
    def _parse_block(self, lines: List[str], start_idx: int) -> Tuple[Dict[str, Any], int]:
        """Parse a KeyValues block starting from the given line index."""
        result = {}
        i = start_idx
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('//'):
                i += 1
                continue
            
            # Handle closing brace
            if line == '}':
                return result, i + 1
            
            # Parse key-value pairs and blocks
            if '"' in line:
                parts = self._split_quoted_line(line)
                if len(parts) >= 1:
                    key = parts[0]

                    # Check if this is a block (next non-empty line is '{')
                    next_line_idx = self._find_next_non_empty(lines, i + 1)
                    if next_line_idx < len(lines) and lines[next_line_idx].strip() == '{':
                        # Parse nested block
                        nested_dict, new_idx = self._parse_block(lines, next_line_idx + 1)
                        result[key] = nested_dict
                        i = new_idx
                    else:
                        # Simple key-value pair (requires a value)
                        value = parts[1] if len(parts) > 1 else ""
                        result[key] = self._convert_value(value)
                        i += 1
                else:
                    i += 1
            else:
                i += 1
        
        return result, i
    
    def _split_quoted_line(self, line: str) -> List[str]:
        """Split a line by quoted strings, handling escaped quotes."""
        parts = []
        current = ""
        in_quotes = False
        escaped = False
        
        for char in line:
            if escaped:
                current += char
                escaped = False
            elif char == '\\':
                escaped = True
                current += char
            elif char == '"':
                if in_quotes:
                    parts.append(current)
                    current = ""
                    in_quotes = False
                else:
                    in_quotes = True
            elif in_quotes:
                current += char
            elif char in [' ', '\t'] and current:
                # Skip whitespace outside quotes
                continue
        
        if current:
            parts.append(current)
        
        return parts
    
    def _find_next_non_empty(self, lines: List[str], start_idx: int) -> int:
        """Find the next non-empty, non-comment line."""
        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith('//'):
                return i
        return len(lines)
    
    def _convert_value(self, value: str) -> Any:
        """Convert string values to appropriate types."""
        if not value:
            return ""
        
        # Try to convert to float
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # Try to convert to int
        try:
            return int(value)
        except ValueError:
            pass
        
        return value


class ItemsGameParser:
    """Parser for items_game.txt file to extract paint kit information."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kv_parser = KeyValuesParser()
    
    def parse_paint_kits(self, items_game_path: str) -> List[Dict[str, Any]]:
        """Extract paint kit information from items_game.txt."""
        self.logger.info(f"Parsing items_game.txt from {items_game_path}")
        
        with open(items_game_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse the entire file
        data = self.kv_parser.parse(content)
        
        paint_kits = []
        paint_kit_sections = []
        
        # Find all paint_kits sections
        def find_paint_kits(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "paint_kits" and isinstance(value, dict):
                        paint_kit_sections.append((path + "." + key if path else key, value))
                    elif isinstance(value, dict):
                        find_paint_kits(value, path + "." + key if path else key)
        
        find_paint_kits(data)
        
        self.logger.info(f"Found {len(paint_kit_sections)} paint_kits sections")
        
        for section_path, paint_kits_data in paint_kit_sections:
            self.logger.info(f"Processing section: {section_path}")
            
            for paint_index_str, paint_data in paint_kits_data.items():
                if not isinstance(paint_data, dict):
                    continue
                
                try:
                    paint_index = int(paint_index_str)
                except ValueError:
                    self.logger.warning(f"Skipping non-numeric paint index: {paint_index_str}")
                    continue
                
                # Extract paint kit information
                description_tag = paint_data.get('description_tag') or paint_data.get('name_tag') or ''
                paint_kit = {
                    'paint_index': paint_index,
                    'paintkit_codename': paint_data.get('name', ''),
                    'description_tag': description_tag,
                    'wear_min': float(paint_data.get('wear_remap_min', 0.0)),
                    'wear_max': float(paint_data.get('wear_remap_max', 1.0))
                }
                
                # Validate wear values
                if paint_kit['wear_min'] < 0 or paint_kit['wear_min'] > 1:
                    self.logger.warning(f"Invalid wear_min {paint_kit['wear_min']} for paint {paint_index}, clamping to [0,1]")
                    paint_kit['wear_min'] = max(0.0, min(1.0, paint_kit['wear_min']))
                
                if paint_kit['wear_max'] < 0 or paint_kit['wear_max'] > 1:
                    self.logger.warning(f"Invalid wear_max {paint_kit['wear_max']} for paint {paint_index}, clamping to [0,1]")
                    paint_kit['wear_max'] = max(0.0, min(1.0, paint_kit['wear_max']))
                
                if paint_kit['wear_min'] >= paint_kit['wear_max']:
                    self.logger.warning(f"wear_min >= wear_max for paint {paint_index}, fixing")
                    if paint_kit['wear_min'] == paint_kit['wear_max']:
                        paint_kit['wear_max'] = min(1.0, paint_kit['wear_min'] + 0.01)
                    else:
                        # Swap to ensure min < max, and pad minimally if needed
                        mn, mx = min(paint_kit['wear_min'], paint_kit['wear_max']), max(paint_kit['wear_min'], paint_kit['wear_max'])
                        if mn == mx:
                            mx = min(1.0, mn + 0.01)
                        paint_kit['wear_min'], paint_kit['wear_max'] = mn, mx
                
                paint_kits.append(paint_kit)
        
        # Remove duplicates by paint_index, keeping the last one
        unique_paint_kits = {}
        for pk in paint_kits:
            unique_paint_kits[pk['paint_index']] = pk
        
        result = list(unique_paint_kits.values())
        result.sort(key=lambda x: x['paint_index'])
        
        self.logger.info(f"Extracted {len(result)} unique paint kits")
        return result


class EnglishTokensParser:
    """Parser for csgo_english.txt to resolve localization tokens."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kv_parser = KeyValuesParser()
    
    def parse_tokens(self, english_path: str) -> Dict[str, str]:
        """Extract English tokens from csgo_english.txt."""
        if not english_path or not Path(english_path).exists():
            self.logger.info("No English tokens file provided or file doesn't exist")
            return {}
        
        self.logger.info(f"Parsing English tokens from {english_path}")
        
        with open(english_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        data = self.kv_parser.parse(content)
        
        # Navigate to Tokens section
        tokens = {}
        if 'lang' in data and isinstance(data['lang'], dict):
            if 'Tokens' in data['lang'] and isinstance(data['lang']['Tokens'], dict):
                tokens = data['lang']['Tokens']
        
        self.logger.info(f"Loaded {len(tokens)} English tokens")
        return tokens


class ExteriorCalculator:
    """Calculate exterior coverage percentages for paint kits."""
    
    # Exterior thresholds
    EXTERIOR_RANGES = {
        'FN': (0.00, 0.07),
        'MW': (0.07, 0.15),
        'FT': (0.15, 0.38),
        'WW': (0.38, 0.45),
        'BS': (0.45, 1.00)
    }
    
    @classmethod
    def calculate_coverage(cls, wear_min: float, wear_max: float) -> Dict[str, Any]:
        """Calculate exterior coverage percentages for a paint kit."""
        result = {}
        
        # Ensure valid range
        wear_range = max(1e-9, wear_max - wear_min)
        
        for exterior, (range_min, range_max) in cls.EXTERIOR_RANGES.items():
            # Calculate overlap between wear range and exterior range
            overlap_start = max(wear_min, range_min)
            overlap_end = min(wear_max, range_max)
            overlap = max(0, overlap_end - overlap_start)
            
            # Calculate percentage
            percentage = round((overlap / wear_range) * 100, 5)
            
            result[f'has_{exterior.lower()}'] = percentage > 0
            result[f'pct_{exterior.lower()}'] = percentage
        
        return result


def main():
    parser = argparse.ArgumentParser(description='Parse CS2 items_game.txt for paint kit float caps')
    parser.add_argument('--items', required=True, help='Path to items_game.txt')
    parser.add_argument('--english', help='Path to csgo_english.txt')
    parser.add_argument('--caps-out', required=True, help='Output path for paint kit caps CSV')
    parser.add_argument('--normal-in', help='Input path for normal CSFloat catalog CSV')
    parser.add_argument('--stattrak-in', help='Input path for StatTrak CSFloat catalog CSV')
    parser.add_argument('--normal-out', help='Output path for enriched normal catalog CSV')
    parser.add_argument('--stattrak-out', help='Output path for enriched StatTrak catalog CSV')
    parser.add_argument('--union-out', help='Output path for consolidated enriched catalog CSV')
    parser.add_argument('--csfloat-like-out', help='Output path for a CSFloat-like catalog CSV (Arma, Coleccion, Grado, FloatMin, FloatMax)')
    parser.add_argument('--tradeups-in', help='Path to TradeUps-like CSV with columns: Skin Name,Rarity,Collection (optional Introduced)')
    parser.add_argument('--reconcile-out', help='Output path for reconciliation CSV vs TradeUps list')
    parser.add_argument('--log-level', default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    log_dir = Path(args.caps_out).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / 'items_game_parse.log'
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting CS2 Items Game Float Caps ETL Pipeline")
    
    try:
        # Parse items_game.txt
        items_parser = ItemsGameParser()
        paint_kits = items_parser.parse_paint_kits(args.items)
        
        # Parse English tokens if provided
        tokens = {}
        if args.english:
            english_parser = EnglishTokensParser()
            tokens = english_parser.parse_tokens(args.english)
        
        # Resolve English names
        for paint_kit in paint_kits:
            description_tag = paint_kit['description_tag']
            token_key = description_tag.lstrip('#') if description_tag else ''
            if token_key and token_key in tokens:
                paint_kit['name_en'] = tokens[token_key]
            elif description_tag and description_tag in tokens:
                # Fallback, in case tokens include leading '#'
                paint_kit['name_en'] = tokens[description_tag]
            else:
                paint_kit['name_en'] = ''
        
        # Build a mapping from unique English skin name to paint_index (only if resolvable)
        name_to_index: Dict[str, int] = {}
        name_counts: Dict[str, int] = {}
        for pk in paint_kits:
            name_en = (pk.get('name_en') or '').strip()
            if not name_en:
                continue
            key = name_en.lower()
            name_counts[key] = name_counts.get(key, 0) + 1
        for pk in paint_kits:
            name_en = (pk.get('name_en') or '').strip()
            if not name_en:
                continue
            key = name_en.lower()
            if name_counts.get(key, 0) == 1:
                name_to_index[key] = int(pk['paint_index'])
        
        # Write paint kit caps CSV
        # Ensure output directory exists
        Path(args.caps_out).parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Writing paint kit caps to {args.caps_out}")
        with open(args.caps_out, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'paint_index', 'paintkit_codename', 'description_tag', 'name_en', 'wear_min', 'wear_max'
            ])
            writer.writeheader()
            writer.writerows(paint_kits)
        
        # Create paint kit lookup
        paint_kit_lookup = {pk['paint_index']: pk for pk in paint_kits}
        
        # Process CSFloat catalogs if provided
        if args.normal_in and args.normal_out:
            process_csfloat_catalog(
                args.normal_in, args.normal_out, paint_kit_lookup, 'normal', logger, name_to_index
            )
        
        if args.stattrak_in and args.stattrak_out:
            process_csfloat_catalog(
                args.stattrak_in, args.stattrak_out, paint_kit_lookup, 'stattrak', logger, name_to_index
            )
        
        # Create consolidated catalog if requested
        if args.union_out and args.normal_out and args.stattrak_out:
            create_consolidated_catalog(args.normal_out, args.stattrak_out, args.union_out, logger)
        
        # Build CSFloat-like rows (for optional outputs and reconciliation)
        cs_rows = build_csfloat_like_rows(args.items, tokens, paint_kit_lookup, logger)
        
        # Create CSFloat-like catalog if requested
        if args.csfloat_like_out:
            write_csfloat_like_catalog(cs_rows, args.csfloat_like_out, logger)
        
        # Reconcile with TradeUps list if requested
        if args.tradeups_in and args.reconcile_out:
            reconcile_with_tradeups(args.tradeups_in, cs_rows, args.reconcile_out, logger)
        
        # Save state
        state_path = Path(args.caps_out).parent / 'items_game_parse_state.json'
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state = {
            'timestamp': datetime.now().isoformat(),
            'paint_kits_processed': len(paint_kits),
            'min_paint_index': min(pk['paint_index'] for pk in paint_kits) if paint_kits else None,
            'max_paint_index': max(pk['paint_index'] for pk in paint_kits) if paint_kits else None,
            'tokens_loaded': len(tokens)
        }
        
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("ETL pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        sys.exit(1)


def process_csfloat_catalog(input_path: str, output_path: str, paint_kit_lookup: Dict[int, Dict], 
                           category: str, logger, name_to_index: Optional[Dict[str, int]] = None):
    """Process a CSFloat catalog and enrich it with paint kit data."""
    logger.info(f"Processing {category} CSFloat catalog: {input_path}")
    
    total_rows = 0
    rows_with_paint_index = 0
    matched_count = 0
    unmatched_count = 0
    unmatched_paint_indexes = set()
    enriched_rows: List[Dict[str, Any]] = []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            total_rows += 1

            enriched_row = dict(row)

            # Attempt to read paint_index if present in any common casing
            paint_index_val: Optional[int] = None
            for key in ('paint_index', 'PaintIndex', 'paintId', 'paint_id', 'paintkit', 'PaintKit'):
                if key in row and str(row[key]).strip() != '':
                    try:
                        paint_index_val = int(float(str(row[key]).strip()))
                        break
                    except ValueError:
                        continue

            if paint_index_val is not None:
                rows_with_paint_index += 1
                pk = paint_kit_lookup.get(paint_index_val)
                if pk:
                    wear_min = float(pk['wear_min'])
                    wear_max = float(pk['wear_max'])
                    coverage = ExteriorCalculator.calculate_coverage(wear_min, wear_max)
                    enriched_row.update({
                        'wear_min_schema': wear_min,
                        'wear_max_schema': wear_max,
                        'has_fn': coverage['has_fn'],
                        'has_mw': coverage['has_mw'],
                        'has_ft': coverage['has_ft'],
                        'has_ww': coverage['has_ww'],
                        'has_bs': coverage['has_bs'],
                        'pct_fn': coverage['pct_fn'],
                        'pct_mw': coverage['pct_mw'],
                        'pct_ft': coverage['pct_ft'],
                        'pct_ww': coverage['pct_ww'],
                        'pct_bs': coverage['pct_bs'],
                    })
                    matched_count += 1
                else:
                    # No matching paint kit found
                    unmatched_count += 1
                    unmatched_paint_indexes.add(paint_index_val)
                    enriched_row.update({
                        'wear_min_schema': '',
                        'wear_max_schema': '',
                        'has_fn': False,
                        'has_mw': False,
                        'has_ft': False,
                        'has_ww': False,
                        'has_bs': False,
                        'pct_fn': 0.0,
                        'pct_mw': 0.0,
                        'pct_ft': 0.0,
                        'pct_ww': 0.0,
                        'pct_bs': 0.0,
                    })
            else:
                # No paint_index column; attempt derivation via English skin name if possible
                derived_index: Optional[int] = None
                # Try common columns to extract a display name like "Weapon | Skin"
                arma_val = (row.get('Arma') or row.get('Name') or row.get('MarketHashName') or row.get('item_name') or '').strip()
                skin_name: Optional[str] = None
                if arma_val:
                    # Expect format "Weapon | Skin"; take the part after '|'
                    if '|' in arma_val:
                        try:
                            skin_name = arma_val.split('|', 1)[1].strip()
                        except Exception:
                            skin_name = None
                    else:
                        skin_name = arma_val.strip()
                if not skin_name:
                    # Try explicit skin fields
                    skin_name = (row.get('Skin') or row.get('skin') or row.get('Nombre') or '').strip() or None
                if skin_name and name_to_index:
                    key = skin_name.lower()
                    if key in name_to_index:
                        derived_index = name_to_index[key]

                if derived_index is not None:
                    pk = paint_kit_lookup.get(derived_index)
                    if pk:
                        wear_min = float(pk['wear_min'])
                        wear_max = float(pk['wear_max'])
                        coverage = ExteriorCalculator.calculate_coverage(wear_min, wear_max)
                        enriched_row.update({
                            'paint_index': derived_index,
                            'wear_min_schema': wear_min,
                            'wear_max_schema': wear_max,
                            'has_fn': coverage['has_fn'],
                            'has_mw': coverage['has_mw'],
                            'has_ft': coverage['has_ft'],
                            'has_ww': coverage['has_ww'],
                            'has_bs': coverage['has_bs'],
                            'pct_fn': coverage['pct_fn'],
                            'pct_mw': coverage['pct_mw'],
                            'pct_ft': coverage['pct_ft'],
                            'pct_ww': coverage['pct_ww'],
                            'pct_bs': coverage['pct_bs'],
                        })
                        matched_count += 1
                    else:
                        unmatched_count += 1
                        unmatched_paint_indexes.add(derived_index)
                        enriched_row.update({
                            'paint_index': derived_index,
                            'wear_min_schema': '',
                            'wear_max_schema': '',
                            'has_fn': False,
                            'has_mw': False,
                            'has_ft': False,
                            'has_ww': False,
                            'has_bs': False,
                            'pct_fn': 0.0,
                            'pct_mw': 0.0,
                            'pct_ft': 0.0,
                            'pct_ww': 0.0,
                            'pct_bs': 0.0,
                        })
                else:
                    # Leave enrichment blank per spec
                    enriched_row.update({
                        'wear_min_schema': '',
                        'wear_max_schema': '',
                        'has_fn': False,
                        'has_mw': False,
                        'has_ft': False,
                        'has_ww': False,
                        'has_bs': False,
                        'pct_fn': 0.0,
                        'pct_mw': 0.0,
                        'pct_ft': 0.0,
                        'pct_ww': 0.0,
                        'pct_bs': 0.0,
                    })
            
            enriched_rows.append(enriched_row)
    
    # Write enriched catalog
    if enriched_rows:
        # Union of all keys to capture potential schema drift across rows
        all_keys = set()
        for r in enriched_rows:
            all_keys.update(r.keys())
        fieldnames = list(all_keys)
        # Deterministic ordering: sort fieldnames alphabetically, but keep original
        # leading columns if present
        preferred_order = [
            'paint_index', 'paintkit', 'weapon', 'skin', 'Arma', 'Coleccion', 'Grado',
            'FloatMin', 'FloatMax', 'wear_min_schema', 'wear_max_schema',
            'has_fn', 'has_mw', 'has_ft', 'has_ww', 'has_bs',
            'pct_fn', 'pct_mw', 'pct_ft', 'pct_ww', 'pct_bs'
        ]
        ordered = [c for c in preferred_order if c in fieldnames]
        remaining = sorted([c for c in fieldnames if c not in ordered])
        fieldnames = ordered + remaining
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_rows)
    
    logger.info(
        "Processed %d rows; rows_with_paint_index=%d; matched=%d; unmatched=%d",
        len(enriched_rows), rows_with_paint_index, matched_count, unmatched_count,
    )
    if rows_with_paint_index:
        coverage_pct = (matched_count / max(1, rows_with_paint_index)) * 100
        logger.info("Join coverage: %.2f%% of rows with paint_index enriched", coverage_pct)
        if coverage_pct < 95.0:
            sample_unmatched = list(sorted(unmatched_paint_indexes))[:20]
            logger.warning(
                "Coverage below 95%%. Example unmatched paint_index values (up to 20 shown): %s",
                sample_unmatched,
            )


def create_consolidated_catalog(normal_path: str, stattrak_path: str, output_path: str, logger):
    """Create a consolidated catalog from normal and StatTrak catalogs."""
    logger.info(f"Creating consolidated catalog: {output_path}")
    
    consolidated_rows = []
    
    # Read normal catalog
    with open(normal_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['category'] = 'normal'
            consolidated_rows.append(row)
    
    # Read StatTrak catalog
    with open(stattrak_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['category'] = 'stattrak'
            consolidated_rows.append(row)
    
    # Write consolidated catalog
    if consolidated_rows:
        # Union of columns across both inputs
        all_cols = set()
        for r in consolidated_rows:
            all_cols.update(r.keys())
        fieldnames = sorted(list(all_cols))
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(consolidated_rows)
    
    logger.info(f"Created consolidated catalog with {len(consolidated_rows)} rows")


def build_csfloat_like_rows(items_game_path: str, tokens: Dict[str, str], paint_kit_lookup: Dict[int, Dict], logger) -> List[Dict[str, Any]]:
    """Build rows for a CSFloat-like catalog (without writing).
    Returns list of dicts with keys: Arma, Coleccion, Grado, FloatMin, FloatMax.
    """
    with open(items_game_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    kv = KeyValuesParser().parse(content)

    # Build paintkit codename -> rarity from paint_kits_rarity
    codename_to_rarity: Dict[str, str] = {}

    def collect_rarity(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == 'paint_kits_rarity' and isinstance(v, dict):
                    for cname, rarity in v.items():
                        if isinstance(rarity, str):
                            codename_to_rarity[cname] = rarity.lower()
                elif isinstance(v, dict):
                    collect_rarity(v)

    collect_rarity(kv)

    rarity_to_grado = {
        # Valve → CS grades
        'common': 'consumer',
        'uncommon': 'industrial',
        'rare': 'mil-spec',
        'mythical': 'restricted',
        'legendary': 'classified',
        'ancient': 'covert',
        'immortal': 'contraband',
    }

    entries = []

    def process_item_sets(obj):
        if not isinstance(obj, dict):
            return
        if 'item_sets' in obj and isinstance(obj['item_sets'], dict):
            sets = obj['item_sets']
            for _, set_val in sets.items():
                if not isinstance(set_val, dict):
                    continue
                is_collection = str(set_val.get('is_collection', '0')).strip() == '1'
                if not is_collection:
                    continue
                name_token = set_val.get('name', '')
                collection_name = ''
                if isinstance(name_token, str):
                    token_key = name_token.lstrip('#')
                    collection_name = tokens.get(token_key, tokens.get(name_token, name_token))
                items = set_val.get('items', {})
                if isinstance(items, dict):
                    for item_key in items.keys():
                        codename = None
                        weapon_code = None
                        m = re.match(r"\[(?P<code>[^\]]+)\](?P<weapon>weapon_[a-z0-9_]+)", str(item_key))
                        if m:
                            codename = m.group('code')
                            weapon_code = m.group('weapon')
                        else:
                            m2 = re.match(r"\[(?P<code>[^\]]+)\]", str(item_key))
                            if m2:
                                codename = m2.group('code')
                        if not codename:
                            continue
                        entries.append((collection_name, codename, weapon_code))
        for _, v in obj.items():
            if isinstance(v, dict):
                process_item_sets(v)

    process_item_sets(kv)

    weapon_map = {
        'weapon_ak47': 'AK-47',
        'weapon_m4a1_silencer': 'M4A1-S',
        'weapon_m4a1': 'M4A4',
        'weapon_awp': 'AWP',
        'weapon_hkp2000': 'P2000',
        'weapon_usp_silencer': 'USP-S',
        'weapon_glock': 'Glock-18',
        'weapon_fiveseven': 'Five-SeveN',
        'weapon_deagle': 'Desert Eagle',
        'weapon_p250': 'P250',
        'weapon_tec9': 'Tec-9',
        'weapon_cz75a': 'CZ75-Auto',
        'weapon_elite': 'Dual Berettas',
        'weapon_p90': 'P90',
        'weapon_mp9': 'MP9',
        'weapon_mp7': 'MP7',
        'weapon_mac10': 'MAC-10',
        'weapon_ump45': 'UMP-45',
        'weapon_bizon': 'PP-Bizon',
        'weapon_galilar': 'Galil AR',
        'weapon_sg556': 'SG 553',
        'weapon_aug': 'AUG',
        'weapon_famas': 'FAMAS',
        'weapon_g3sg1': 'G3SG1',
        'weapon_scar20': 'SCAR-20',
        'weapon_ssg08': 'SSG 08',
        'weapon_nova': 'Nova',
        'weapon_xm1014': 'XM1014',
        'weapon_sawedoff': 'Sawed-Off',
        'weapon_mag7': 'MAG-7',
        'weapon_m249': 'M249',
        'weapon_negev': 'Negev',
        # Knives and others can be added as needed
    }

    rows = []
    codename_to_paint = {pk['paintkit_codename']: pk for pk in paint_kit_lookup.values()}
    for collection_name, codename, weapon_code in entries:
        pk = codename_to_paint.get(codename)
        if not pk:
            continue
        name_en = (pk.get('name_en') or '').strip() or (pk.get('description_tag') or '')
        wear_min = float(pk.get('wear_min', 0.0))
        wear_max = float(pk.get('wear_max', 1.0))
        rarity_valve = codename_to_rarity.get(codename, '').lower()
        grado = rarity_to_grado.get(rarity_valve, '')
        weapon_disp = weapon_map.get(weapon_code or '', (weapon_code or '').replace('weapon_', '').upper())
        arma = f"{weapon_disp} | {name_en}" if name_en else weapon_disp
        coleccion = collection_name or ''
        rows.append({'Arma': arma, 'Coleccion': coleccion, 'Grado': grado, 'FloatMin': wear_min, 'FloatMax': wear_max})
    rows.sort(key=lambda r: r['Arma'])
    return rows


def write_csfloat_like_catalog(rows: List[Dict[str, Any]], output_path: str, logger):
    logger.info(f"Creating CSFloat-like catalog: {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Arma', 'Coleccion', 'Grado', 'FloatMin', 'FloatMax'])
        writer.writeheader()
        writer.writerows(rows)
    logger.info(f"CSFloat-like catalog written with {len(rows)} rows")


def reconcile_with_tradeups(tradeups_path: str, cs_rows: List[Dict[str, Any]], output_path: str, logger):
    """Reconcile an external TradeUps list against our CSFloat-like rows.
    tradeups CSV expected columns at least: Skin Name,Rarity,Collection
    We'll build an Arma string from Skin Name (expects format "Weapon Skin" or "Weapon Lightning Strike").
    """
    logger.info(f"Reconciling TradeUps list: {tradeups_path}")
    # Build index for our rows by Arma (case-insensitive)
    our_index = {r['Arma'].lower(): r for r in cs_rows}
    out_rows: List[Dict[str, Any]] = []
    with open(tradeups_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skin_name = (row.get('Skin Name') or '').strip()
            rarity = (row.get('Rarity') or '').strip()
            collection = (row.get('Collection') or '').strip()
            if not skin_name:
                continue
            # Normalize: TradeUps may have format "AWP Lightning Strike"; convert to "AWP | Lightning Strike"
            arma_key = skin_name.replace(' | ', ' ').strip()
            parts = arma_key.split(' ', 1)
            arma_display = skin_name
            if len(parts) == 2:
                arma_display = f"{parts[0]} | {parts[1]}"
            key = arma_display.lower()
            ours = our_index.get(key)
            if not ours:
                out_rows.append({
                    'Arma': arma_display,
                    'TradeUps_Collection': collection,
                    'Items_Collection': '',
                    'TradeUps_Rarity': rarity,
                    'Items_Grado': '',
                    'Match_Collection': False,
                    'Match_Rarity': False,
                    'Note': 'Not found in items_game sets'
                })
                continue
            match_collection = collection.lower() == (ours['Coleccion'] or '').lower()
            match_rarity = rarity.lower() == (ours['Grado'] or '').lower()
            out_rows.append({
                'Arma': arma_display,
                'TradeUps_Collection': collection,
                'Items_Collection': ours['Coleccion'],
                'TradeUps_Rarity': rarity,
                'Items_Grado': ours['Grado'],
                'Match_Collection': match_collection,
                'Match_Rarity': match_rarity,
                'Note': ''
            })
    # Write reconciliation
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'Arma', 'TradeUps_Collection', 'Items_Collection', 'TradeUps_Rarity', 'Items_Grado', 'Match_Collection', 'Match_Rarity', 'Note'
        ])
        writer.writeheader()
        writer.writerows(out_rows)
    logger.info(f"Reconciliation written with {len(out_rows)} rows to {output_path}")


if __name__ == '__main__':
    main()