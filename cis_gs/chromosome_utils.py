"""
Advanced Chromosome Utilities for Cis-GS
Handles multiple genome annotation formats and creates professional visualizations
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Polygon
import numpy as np
from pathlib import Path


def extract_chromosome_from_record_id(record_id):
    """
    Extract chromosome information from various record ID formats
    
    Supported formats:
    1. Arachis annotation 1: arahy.Tifrunner.gnm1.ann1.G3JQSN.v1.0|arahy.Tifrunner.gnm1.ann1.G3JQSN|arahy.Tifrunner.gnm1.Arahy.16:99203542-99205541(-)
       → Chromosome: Arahy.16 or Chr16
    
    2. Arachis annotation 2 / NCBI: gene-LOC112737217|LOC112737217|NC_092048.1:11811317-11813316(-)
       → Chromosome: NC_092048.1
    
    3. Medicago: gene-LOC11437652|LOC11437652|NC_053045.1:51900477-51901476(-)
       → Chromosome: NC_053045.1
    
    4. Arabidopsis: AT1G12345 or Chr1:1000-2000
       → Chromosome: Chr1
    
    Returns:
    --------
    tuple: (chromosome_name, genomic_position)
    """
    
    record_id = str(record_id).strip()
    
    # Method 1: Extract from pipe-delimited format (most common in your data)
    if '|' in record_id:
        parts = record_id.split('|')
        # Look for the part with coordinates (has ':' and '-')
        for part in parts:
            if ':' in part and '-' in part:
                # Extract chromosome and position
                # Format: NC_092048.1:11811317-11813316(-) or arahy.Tifrunner.gnm1.Arahy.16:99203542-99205541(-)
                coord_part = part.split(':')[0]
                position_part = part.split(':')[1] if ':' in part else None
                
                # Extract genomic position
                genomic_pos = None
                if position_part:
                    pos_match = re.search(r'(\d+)-(\d+)', position_part)
                    if pos_match:
                        genomic_pos = int(pos_match.group(1))
                
                # For Arachis style: arahy.Tifrunner.gnm1.Arahy.16 → extract '16'
                if 'Arahy' in coord_part or 'arahy' in coord_part.lower():
                    chr_match = re.search(r'\.([A-Za-z]+)\.(\d+)', coord_part)
                    if chr_match:
                        return f"Chr{chr_match.group(2)}", genomic_pos
                
                # For NC_ RefSeq format: NC_092048.1 → keep as is, but try to get chromosome number
                if coord_part.startswith('NC_') or coord_part.startswith('NW_'):
                    # Try to map RefSeq to chromosome number (if possible from data)
                    return coord_part, genomic_pos
                
                # For other formats with chromosome in name
                chr_match = re.search(r'[Cc]hr[_\.]?(\d+|[IVXLCDM]+|[A-Z])', coord_part)
                if chr_match:
                    return f"Chr{chr_match.group(1)}", genomic_pos
                
                return coord_part, genomic_pos
    
    # Method 2: Arabidopsis AT gene format
    if record_id.startswith('AT') or record_id.startswith('At'):
        chr_num = record_id[2] if len(record_id) > 2 else '0'
        if chr_num.isdigit():
            return f"Chr{chr_num}", None
    
    # Method 3: Direct chromosome format (Chr1:1000-2000)
    if record_id.startswith('Chr') or record_id.startswith('chr'):
        if ':' in record_id:
            chr_part = record_id.split(':')[0]
            pos_match = re.search(r'(\d+)-', record_id)
            genomic_pos = int(pos_match.group(1)) if pos_match else None
            return chr_part, genomic_pos
        else:
            return record_id.split('_')[0], None
    
    # Method 4: NC_ RefSeq without pipes
    if record_id.startswith('NC_') or record_id.startswith('NW_'):
        if ':' in record_id:
            chr_part = record_id.split(':')[0]
            pos_match = re.search(r'(\d+)-', record_id)
            genomic_pos = int(pos_match.group(1)) if pos_match else None
            return chr_part, genomic_pos
        return record_id, None
    
    # Default: return as-is
    return record_id, None


def normalize_chromosome_name(chr_name):
    """
    Normalize chromosome names for consistent sorting and display
    """
    if not chr_name:
        return "Unknown"
    
    chr_name = str(chr_name).strip()
    
    # Extract number if present
    num_match = re.search(r'(\d+)', chr_name)
    if num_match:
        num = num_match.group(1)
        return f"Chr{num}"
    
    # Keep RefSeq IDs as-is
    if chr_name.startswith('NC_') or chr_name.startswith('NW_'):
        return chr_name
    
    return chr_name


def create_refseq_to_chromosome_map(df):
    """
    Attempt to create a mapping from RefSeq IDs to chromosome numbers
    based on the data itself
    """
    mapping = {}
    
    # Group by chromosome and look for patterns
    chr_groups = df.groupby('chromosome')
    
    for chr_name, group in chr_groups:
        if chr_name.startswith('NC_'):
            # Try to infer chromosome number from gene IDs or other columns
            # This is a heuristic - in practice you'd have a reference mapping
            pass
    
    return mapping


def add_chromosome_column(df):
    """
    Add chromosome and genomic_position columns to the dataframe
    """
    if df.empty:
        return df
    
    df = df.copy()
    
    # Extract chromosome and position
    chr_data = df['record_id'].apply(extract_chromosome_from_record_id)
    df['chromosome'] = chr_data.apply(lambda x: x[0])
    df['genomic_position'] = chr_data.apply(lambda x: x[1])
    
    # Normalize chromosome names
    df['chromosome_normalized'] = df['chromosome'].apply(normalize_chromosome_name)
    
    return df


def plot_chromosome_with_hits(df, chromosome, output_path, 
                               show_gene_names=True, 
                               figsize=(16, 8),
                               dpi=300):
    """
    Create a detailed visualization of a single chromosome with all motif hits
    Shows both strands with genes and cis-elements
    
    Parameters:
    -----------
    df : DataFrame
        Must have: chromosome, gene_id, gene_name, motif_name, 
                  genomic_position, start_1based, strand
    chromosome : str
        Chromosome to visualize
    output_path : str
        Where to save the figure
    show_gene_names : bool
        Show gene names
    """
    
    # Filter for this chromosome
    chr_data = df[df['chromosome'] == chromosome].copy()
    
    if chr_data.empty:
        raise ValueError(f"No data for {chromosome}")
    
    # Determine chromosome length
    if chr_data['genomic_position'].notna().any():
        max_pos = chr_data['genomic_position'].max()
        chr_length = max_pos * 1.1
    else:
        # Estimate from number of genes
        chr_length = len(chr_data) * 5000  # Assume 5kb per gene
    
    # Separate forward and reverse strands
    forward_data = chr_data[chr_data.get('strand', '+') == '+']
    reverse_data = chr_data[chr_data.get('strand', '+') == '-']
    
    # Pre-calculate all positions and offsets to determine needed figure height
    # This ensures we have enough vertical space for all labels
    temp_plotted_forward = []
    max_forward_offset = 0
    label_width = chr_length * 0.05  # Increased from 0.03 to prevent overlaps better
    
    for idx, hit in forward_data.iterrows():
        x_pos = hit['genomic_position'] if pd.notna(hit['genomic_position']) else idx * (chr_length / len(forward_data))
        y_offset = 0
        for prev_x, prev_y_offset in temp_plotted_forward:
            if abs(prev_x - x_pos) < label_width:
                y_offset = max(y_offset, prev_y_offset + 2)  # Increased spacing
        temp_plotted_forward.append((x_pos, y_offset))
        max_forward_offset = max(max_forward_offset, y_offset)
    
    temp_plotted_reverse = []
    max_reverse_offset = 0
    
    for idx, hit in reverse_data.iterrows():
        x_pos = hit['genomic_position'] if pd.notna(hit['genomic_position']) else idx * (chr_length / len(reverse_data))
        y_offset = 0
        for prev_x, prev_y_offset in temp_plotted_reverse:
            if abs(prev_x - x_pos) < label_width:
                y_offset = max(y_offset, prev_y_offset + 2)  # Increased spacing
        temp_plotted_reverse.append((x_pos, y_offset))
        max_reverse_offset = max(max_reverse_offset, y_offset)
    
    # Calculate needed vertical space
    # Each unit of offset needs approximately 0.8-1.0 inches of vertical space
    base_height = figsize[1]
    needed_height = base_height + (max_forward_offset + max_reverse_offset) * 0.4
    dynamic_figsize = (figsize[0], max(base_height, min(needed_height, 20)))  # Cap at 20 inches
    
    # Create figure with dynamic height
    fig, ax = plt.subplots(figsize=dynamic_figsize)
    
    # Draw chromosome backbone
    backbone_y_forward = 0.7
    backbone_y_reverse = -0.7
    
    # Forward strand (top)
    ax.plot([0, chr_length], [backbone_y_forward, backbone_y_forward], 
           color='#2C3E50', linewidth=12, solid_capstyle='round', 
           label='Forward Strand (+)', zorder=1)
    
    # Add forward strand label
    ax.text(-chr_length*0.03, backbone_y_forward, '(+) Strand', 
           fontsize=11, ha='right', va='center', fontweight='bold',
           color='#2C3E50',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='#2C3E50', linewidth=2))
    
    # Reverse strand (bottom)
    ax.plot([0, chr_length], [backbone_y_reverse, backbone_y_reverse], 
           color='#7F8C8D', linewidth=12, solid_capstyle='round', 
           label='Reverse Strand (-)', zorder=1)
    
    # Add reverse strand label
    ax.text(-chr_length*0.03, backbone_y_reverse, '(−) Strand', 
           fontsize=11, ha='right', va='center', fontweight='bold',
           color='#7F8C8D',
           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                    edgecolor='#7F8C8D', linewidth=2))
    
    # Color mapping for motifs
    unique_motifs = sorted(df['motif_name'].unique())
    colors = plt.cm.Set3(np.linspace(0, 1, len(unique_motifs)))
    motif_colors = {motif: colors[i] for i, motif in enumerate(unique_motifs)}
    
    # Plot hits on forward strand (use pre-calculated offsets)
    for idx, (hit, (x_pos, y_offset)) in enumerate(zip(forward_data.iterrows(), temp_plotted_forward)):
        hit = hit[1]  # Get the row data from iterrows tuple
        
        y_label = backbone_y_forward + 2 + y_offset
        
        # Draw line from backbone to label position - NOW TOUCHES THE BACKBONE
        color = motif_colors.get(hit['motif_name'], '#E74C3C')
        ax.plot([x_pos, x_pos], [backbone_y_forward, y_label], 
               color=color, linewidth=2, alpha=0.7, zorder=2)
        
        # Draw hit marker
        ax.scatter(x_pos, y_label, s=100, c=[color], 
                  edgecolors='black', linewidths=1.5, 
                  zorder=3, marker='o')
        
        # Add gene/motif label
        if show_gene_names:
            label = f"{hit.get('gene_name', hit.get('gene_id', ''))}\n{hit['motif_name']}"
            ax.text(x_pos, y_label, label,  
                   fontsize=8, ha='center', va='center',
                   rotation=45, 
                   bbox=dict(boxstyle='round,pad=0.4', 
                           facecolor='white', 
                           edgecolor=color,
                           alpha=0.9,
                           linewidth=1.5))
    
    # Plot hits on reverse strand (use pre-calculated offsets)
    for idx, (hit, (x_pos, y_offset)) in enumerate(zip(reverse_data.iterrows(), temp_plotted_reverse)):
        hit = hit[1]  # Get the row data from iterrows tuple
        
        y_label = backbone_y_reverse - 1.5 - y_offset
        
        # Draw line from backbone to label position - NOW TOUCHES THE BACKBONE
        color = motif_colors.get(hit['motif_name'], '#3498DB')
        ax.plot([x_pos, x_pos], [backbone_y_reverse, y_label], 
               color=color, linewidth=2, alpha=0.7, zorder=2)
        
        # Draw hit marker
        ax.scatter(x_pos, y_label, s=100, c=[color], 
                  edgecolors='black', linewidths=1.5, 
                  zorder=3, marker='o')
        
        # Add gene/motif label
        if show_gene_names:
            label = f"{hit.get('gene_name', hit.get('gene_id', ''))}\n{hit['motif_name']}"
            ax.text(x_pos, y_label, label, 
                   fontsize=8, ha='center', va='center',
                   rotation=45,
                   bbox=dict(boxstyle='round,pad=0.4', 
                           facecolor='white', 
                           edgecolor=color,
                           alpha=0.9,
                           linewidth=1.5))
    
    # Add position scale
    mb_scale = np.arange(0, chr_length, max(chr_length/10, 1_000_000))
    for pos in mb_scale:
        ax.plot([pos, pos], [0.5, -0.5], 'k-', linewidth=1, alpha=0.3)
        ax.text(pos, 0, f"{pos/1_000_000:.1f}", 
               fontsize=9, ha='center', va='center',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Add final tick at chromosome end to show total length
    ax.plot([chr_length, chr_length], [0.5, -0.5], 'k-', linewidth=1, alpha=0.3)
    ax.text(chr_length, 0, f"{chr_length/1_000_000:.1f}", 
           fontsize=9, ha='center', va='center',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # Add scale label
    ax.text(chr_length/2, -0.8, "Position (Mb)", 
           fontsize=11, ha='center', fontweight='bold')
    
    # Styling
    ax.set_xlim(-chr_length*0.05, chr_length*1.05)
    
    # Adjust ylim based on number of overlapping hits
    # temp_plotted positions store (x_pos, y_offset) tuples
    # Actual y positions: forward = backbone_y_forward + 1.5 + y_offset
    #                     reverse = backbone_y_reverse - 1.5 - y_offset
    max_y = max([backbone_y_forward + 1.5 + off for _, off in temp_plotted_forward], default=backbone_y_forward + 1.5) + 2
    min_y = min([backbone_y_reverse - 1.5 - off for _, off in temp_plotted_reverse], default=backbone_y_reverse - 1.5) - 2
    ax.set_ylim(min_y, max_y)
    
    ax.set_xlabel("Genomic Position", fontsize=12, fontweight='bold')
    ax.set_title(f"{chromosome} - Motif Hits", fontsize=14, fontweight='bold')
    ax.axis('off')
    
    # Legend for motifs
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', 
              markerfacecolor=motif_colors[motif], 
              markersize=10, label=motif,
              markeredgecolor='black', markeredgewidth=1)
        for motif in unique_motifs
    ]
    
    ax.legend(handles=legend_elements, 
             loc='upper left', 
             bbox_to_anchor=(1.02, 1),
             fontsize=10,
             title='Motifs',
             title_fontsize=11,
             frameon=True,
             fancybox=True)
    
    # Add summary
    total_hits = len(chr_data)
    forward_hits = len(forward_data)
    reverse_hits = len(reverse_data)
    
    summary = f"Total hits: {total_hits} | Forward: {forward_hits} | Reverse: {reverse_hits}"
    plt.figtext(0.5, 0.02, summary, ha='center', fontsize=10,
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    # Save
    output_path = Path(output_path)
    if output_path.suffix.lower() == '.svg':
        plt.savefig(output_path, format='svg', dpi=dpi, bbox_inches='tight')
    else:
        plt.savefig(output_path, format='png', dpi=dpi, bbox_inches='tight')
    
    plt.close(fig)
    
    return str(output_path)


# Example usage
if __name__ == "__main__":
    # Test chromosome extraction
    test_ids = [
        "arahy.Tifrunner.gnm1.ann1.G3JQSN.v1.0|arahy.Tifrunner.gnm1.ann1.G3JQSN|arahy.Tifrunner.gnm1.Arahy.16:99203542-99205541(-)",
        "gene-LOC112737217|LOC112737217|NC_092048.1:11811317-11813316(-)",
        "gene-LOC11437652|LOC11437652|NC_053045.1:51900477-51901476(-)",
        "AT1G12345",
        "Chr1:1000-2000"
    ]
    
    print("Testing chromosome extraction:")
    for test_id in test_ids:
        chr_name, pos = extract_chromosome_from_record_id(test_id)
        print(f"{test_id[:50]:<50} → {chr_name:<15} (pos: {pos})")
