#!/usr/bin/env python3
import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import phb_details

def load_data():
    """Load the medical data from JSON file"""
    # Check if enhanced data exists, otherwise use regular data
    if os.path.exists('gwendolyn_medical_data_enhanced.json'):
        with open('gwendolyn_medical_data_enhanced.json', 'r') as f:
            data = json.load(f)
    elif os.path.exists('gwendolyn_medical_data.json'):
        with open('gwendolyn_medical_data.json', 'r') as f:
            data = json.load(f)
    else:
        raise FileNotFoundError("No medical data JSON file found")
    
    # Convert date strings to datetime objects
    for item in data:
        if item['date']:
            item['date'] = datetime.strptime(item['date'], '%Y-%m-%d')
    
    return data

def create_phb_timeline(data):
    """Create an enhanced interactive timeline visualization with PHB integration"""
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Sort by date
    df = df.sort_values('date')
    
    # Create a color map for specialties
    specialties = df['specialty'].unique()
    color_map = {specialty: f'rgb({hash(specialty) % 256}, {(hash(specialty) // 256) % 256}, {(hash(specialty) // 65536) % 256})' 
                for specialty in specialties}
    
    # Create figure with subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        specs=[[{"type": "scatter"}], [{"type": "table"}]],
        vertical_spacing=0.1,
        subplot_titles=("Medical Timeline with PHB Integration", "Event Details")
    )
    
    # Add events to the timeline
    for i, row in df.iterrows():
        # Prepare hover text with all available information
        hover_text = f"<b>{row['title']}</b><br>"
        hover_text += f"Date: {row['date'].strftime('%Y-%m-%d')}<br>"
        hover_text += f"Specialty: {row['specialty']}<br>"
        
        # Add personnel if available
        if 'personnel' in row and row['personnel']:
            hover_text += f"Personnel: {', '.join(row['personnel'])}<br>"
        
        # Add hospitals if available
        if 'hospitals' in row and row['hospitals']:
            hover_text += f"Hospitals: {', '.join(row['hospitals'])}<br>"
        
        # Add appointments if available
        if 'appointments' in row and row['appointments']:
            hover_text += f"Appointments: {', '.join(row['appointments'])}<br>"
        
        # Add medications if available
        if 'medications' in row and row['medications']:
            hover_text += f"Medications: {', '.join(row['medications'])}<br>"
        
        # Add procedures if available
        if 'procedures' in row and row['procedures']:
            hover_text += f"Procedures: {', '.join(row['procedures'])}<br>"
        
        # Add diagnoses if available
        if 'diagnoses' in row and row['diagnoses']:
            hover_text += f"Diagnoses: {', '.join(row['diagnoses'])}<br>"
        
        # Add events
        if 'events' in row and row['events']:
            hover_text += f"Events: {', '.join(row['events'][:2])}<br>"
        
        # Add PHB categories if available
        if 'phb_categories' in row and row['phb_categories']:
            phb_cats = [f"{cat['category']} ({cat['severity']})" for cat in row['phb_categories']]
            hover_text += f"PHB Categories: {', '.join(phb_cats)}<br>"
        
        # Add PHB supports if available
        if 'phb_supports' in row and row['phb_supports']:
            phb_sups = [sup['support'] for sup in row['phb_supports']]
            hover_text += f"PHB Supports: {', '.join(phb_sups)}<br>"
        
        # Determine marker size based on PHB relevance
        marker_size = 15
        if 'phb_categories' in row and row['phb_categories']:
            # Larger marker for events with PHB categories
            marker_size = 20
        
        # Determine marker color based on specialty
        marker_color = color_map[row['specialty']]
        
        # Add trace for this event
        fig.add_trace(
            go.Scatter(
                x=[row['date']],
                y=[row['specialty']],
                mode='markers',
                marker=dict(
                    size=marker_size,
                    color=marker_color,
                    line=dict(width=2, color='DarkSlateGrey')
                ),
                name=row['title'],
                text=hover_text,
                hoverinfo='text',
                customdata=[i]  # Store the index for filtering
            ),
            row=1, col=1
        )
    
    # Add table for details
    table_columns = ["Date", "Title", "Specialty", "PHB Categories"]
    table_values = [
        df['date'].dt.strftime('%Y-%m-%d'),
        df['title'],
        df['specialty'],
    ]
    
    # Add PHB categories column
    phb_categories_column = []
    for _, row in df.iterrows():
        if 'phb_categories' in row and row['phb_categories']:
            phb_cats = [f"{cat['category']} ({cat['severity']})" for cat in row['phb_categories']]
            phb_categories_column.append(', '.join(phb_cats))
        else:
            phb_categories_column.append('')
    
    table_values.append(phb_categories_column)
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=table_columns,
                fill_color='rgba(50, 50, 50, 1)',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=table_values,
                fill_color='rgba(30, 30, 30, 0.8)',
                align='left',
                font=dict(color='white', size=11)
            )
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Gwendolyn Vials Moore - Medical History Timeline with PHB Integration",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24)
        },
        xaxis=dict(
            title="Date",
            type='date',
            tickformat='%Y-%m-%d',
            rangeslider=dict(visible=True),
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        ),
        yaxis=dict(
            title="Medical Specialty",
            categoryorder='category ascending'
        ),
        hovermode='closest',
        height=1000,
        template='plotly_dark',
        margin=dict(t=100, b=0, l=0, r=0),
        showlegend=False
    )
    
    # Add annotations for PHB categories
    for category, info in phb_details.PHB_CATEGORIES.items():
        fig.add_annotation(
            x=0.01,
            y=0.99 - (list(phb_details.PHB_CATEGORIES.keys()).index(category) * 0.03),
            xref="paper",
            yref="paper",
            text=f"{category} ({info['severity']})",
            showarrow=False,
            font=dict(size=10, color="white"),
            align="left",
            bgcolor=f"rgba({hash(category) % 256}, {(hash(category) // 256) % 256}, {(hash(category) // 65536) % 256}, 0.5)",
            bordercolor="white",
            borderwidth=1,
            borderpad=4,
            width=200
        )
    
    # Save the figure as JSON for the HTML template
    fig_json = fig.to_json()
    fig_dict = json.loads(fig_json)
    
    # Convert data to JSON for JavaScript
    data_json = []
    for item in data:
        data_item = {
            'title': item['title'],
            'date': item['date'].strftime('%Y-%m-%d') if item['date'] else None,
            'specialty': item['specialty'],
            'content': item['content']
        }
        
        # Add additional fields if they exist
        for field in ['personnel', 'hospitals', 'appointments', 'dates', 
                     'medications', 'procedures', 'diagnoses', 'events',
                     'phb_categories', 'phb_supports']:
            if field in item:
                data_item[field] = item[field]
        
        data_json.append(data_item)
    
    # Create the HTML content with the JSON data embedded
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gwendolyn Vials Moore - Medical History Timeline with PHB Integration</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background-color: #1E1E1E; color: white; font-family: Arial, sans-serif; }}
            .container {{ width: 95%; margin: 20px auto; }}
            h1 {{ text-align: center; margin-bottom: 20px; }}
            .filters {{ margin-bottom: 20px; background-color: #333; padding: 10px; border-radius: 5px; }}
            .filters label {{ margin-right: 10px; }}
            select {{ background-color: #444; color: white; padding: 5px; border: none; border-radius: 3px; }}
            .timeline {{ width: 100%; height: 800px; }}
            .info-panel {{ background-color: #333; padding: 15px; margin-top: 20px; border-radius: 5px; }}
            .info-panel h2 {{ margin-top: 0; }}
            .search-box {{ margin-bottom: 10px; }}
            .search-box input {{ width: 100%; padding: 8px; background-color: #444; color: white; border: none; border-radius: 3px; }}
            .phb-panel {{ background-color: #333; padding: 15px; margin-top: 20px; border-radius: 5px; }}
            .phb-panel h2 {{ margin-top: 0; }}
            .phb-category {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
            .severity-SEVERE {{ background-color: rgba(255, 0, 0, 0.3); }}
            .severity-HIGH {{ background-color: rgba(255, 165, 0, 0.3); }}
            .severity-MODERATE {{ background-color: rgba(255, 255, 0, 0.3); }}
            .tab-container {{ display: flex; margin-bottom: 10px; }}
            .tab {{ padding: 10px 20px; background-color: #444; margin-right: 5px; cursor: pointer; border-radius: 5px 5px 0 0; }}
            .tab.active {{ background-color: #555; }}
            .tab-content {{ display: none; }}
            .tab-content.active {{ display: block; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Gwendolyn Vials Moore - Medical History Timeline with PHB Integration</h1>
            
            <div class="tab-container">
                <div class="tab active" onclick="openTab(event, 'timeline-tab')">Timeline</div>
                <div class="tab" onclick="openTab(event, 'phb-tab')">PHB Details</div>
            </div>
            
            <div id="timeline-tab" class="tab-content active">
                <div class="filters">
                    <label for="specialty-filter">Filter by Specialty:</label>
                    <select id="specialty-filter" onchange="filterBySpecialty()">
                        <option value="all">All Specialties</option>
                        {' '.join([f'<option value="{s}">{s}</option>' for s in sorted(specialties) if s != "Unknown"])}
                    </select>
                    
                    <label for="year-filter" style="margin-left: 20px;">Filter by Year:</label>
                    <select id="year-filter" onchange="filterByYear()">
                        <option value="all">All Years</option>
                        {' '.join([f'<option value="{y}">{y}</option>' for y in sorted(df['date'].dt.year.unique())])}
                    </select>
                    
                    <label for="phb-filter" style="margin-left: 20px;">Filter by PHB Category:</label>
                    <select id="phb-filter" onchange="filterByPHB()">
                        <option value="all">All PHB Categories</option>
                        {' '.join([f'<option value="{c}">{c} ({info["severity"]})</option>' for c, info in phb_details.PHB_CATEGORIES.items()])}
                    </select>
                </div>
                
                <div class="search-box">
                    <input type="text" id="search-input" placeholder="Search for keywords in events, titles, or PHB categories..." onkeyup="searchTimeline()">
                </div>
                
                <div id="timeline" class="timeline"></div>
                
                <div class="info-panel">
                    <h2>Selected Event Details</h2>
                    <div id="event-details">Click on a point in the timeline to see details</div>
                </div>
            </div>
            
            <div id="phb-tab" class="tab-content">
                <div class="phb-panel">
                    <h2>Public Health Budget (PHB) Categories</h2>
                    <div id="phb-categories">
                        {' '.join([f'<div class="phb-category severity-{info["severity"]}"><h3>{category} ({info["severity"]})</h3><p>{info["description"]}</p><ul>{" ".join([f"<li>{detail}</li>" for detail in info["details"]])}</ul></div>' for category, info in phb_details.PHB_CATEGORIES.items()])}
                    </div>
                    
                    <h2>PHB Supports</h2>
                    <div id="phb-supports">
                        {' '.join([f'<div class="phb-category"><h3>{support}</h3><p>{info["description"]}</p><ul>{" ".join([f"<li>{detail}</li>" for detail in info["details"]])}</ul></div>' for support, info in phb_details.PHB_SUPPORTS.items()])}
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Store the original figure data
            let originalData;
            
            // Store the event data
            const eventData = {json.dumps(data_json)};
            
            // Load the Plotly figure
            Plotly.newPlot('timeline', {json.dumps(fig_dict['data'])}, {json.dumps(fig_dict['layout'])});
            
            // Get the original data after plot is created
            document.getElementById('timeline').on('plotly_afterplot', function() {{
                originalData = document.getElementById('timeline').data;
            }});
            
            // Handle click events on the timeline
            document.getElementById('timeline').on('plotly_click', function(data) {{
                const point = data.points[0];
                if (point.customdata) {{
                    const index = point.customdata[0];
                    const event = eventData[index];
                    
                    let detailsHtml = `
                        <h3>${{event.title}}</h3>
                        <p><strong>Date:</strong> ${{event.date}}</p>
                        <p><strong>Specialty:</strong> ${{event.specialty}}</p>
                    `;
                    
                    if (event.personnel) {{
                        detailsHtml += `<p><strong>Personnel:</strong> ${{event.personnel.join(', ')}}</p>`;
                    }}
                    
                    if (event.hospitals) {{
                        detailsHtml += `<p><strong>Hospitals:</strong> ${{event.hospitals.join(', ')}}</p>`;
                    }}
                    
                    if (event.appointments) {{
                        detailsHtml += `<p><strong>Appointments:</strong> ${{event.appointments.join(', ')}}</p>`;
                    }}
                    
                    if (event.medications) {{
                        detailsHtml += `<p><strong>Medications:</strong> ${{event.medications.join(', ')}}</p>`;
                    }}
                    
                    if (event.procedures) {{
                        detailsHtml += `<p><strong>Procedures:</strong> ${{event.procedures.join(', ')}}</p>`;
                    }}
                    
                    if (event.diagnoses) {{
                        detailsHtml += `<p><strong>Diagnoses:</strong> ${{event.diagnoses.join(', ')}}</p>`;
                    }}
                    
                    if (event.events) {{
                        detailsHtml += `<p><strong>Events:</strong></p><ul>`;
                        event.events.forEach(e => {{
                            detailsHtml += `<li>${{e}}</li>`;
                        }});
                        detailsHtml += `</ul>`;
                    }}
                    
                    if (event.phb_categories && event.phb_categories.length > 0) {{
                        detailsHtml += `<p><strong>PHB Categories:</strong></p><ul>`;
                        event.phb_categories.forEach(cat => {{
                            detailsHtml += `<li>${{cat.category}} (${{cat.severity}}): ${{cat.description}}</li>`;
                        }});
                        detailsHtml += `</ul>`;
                    }}
                    
                    if (event.phb_supports && event.phb_supports.length > 0) {{
                        detailsHtml += `<p><strong>PHB Supports:</strong></p><ul>`;
                        event.phb_supports.forEach(sup => {{
                            detailsHtml += `<li>${{sup.support}}: ${{sup.description}}</li>`;
                        }});
                        detailsHtml += `</ul>`;
                    }}
                    
                    detailsHtml += `<p><strong>Content:</strong> ${{event.content}}</p>`;
                    
                    document.getElementById('event-details').innerHTML = detailsHtml;
                }}
            }});
            
            // Filter by specialty
            function filterBySpecialty() {{
                const specialty = document.getElementById('specialty-filter').value;
                const yearFilter = document.getElementById('year-filter').value;
                const phbFilter = document.getElementById('phb-filter').value;
                
                applyFilters(specialty, yearFilter, phbFilter);
            }}
            
            // Filter by year
            function filterByYear() {{
                const specialty = document.getElementById('specialty-filter').value;
                const year = document.getElementById('year-filter').value;
                const phbFilter = document.getElementById('phb-filter').value;
                
                applyFilters(specialty, year, phbFilter);
            }}
            
            // Filter by PHB category
            function filterByPHB() {{
                const specialty = document.getElementById('specialty-filter').value;
                const year = document.getElementById('year-filter').value;
                const phbCategory = document.getElementById('phb-filter').value;
                
                applyFilters(specialty, year, phbCategory);
            }}
            
            // Apply all filters
            function applyFilters(specialty, year, phbCategory) {{
                let filteredData = eventData;
                
                // Apply specialty filter
                if (specialty !== 'all') {{
                    filteredData = filteredData.filter(event => event.specialty === specialty);
                }}
                
                // Apply year filter
                if (year !== 'all') {{
                    filteredData = filteredData.filter(event => {{
                        const eventDate = new Date(event.date);
                        return eventDate.getFullYear().toString() === year;
                    }});
                }}
                
                // Apply PHB category filter
                if (phbCategory !== 'all') {{
                    filteredData = filteredData.filter(event => {{
                        if (!event.phb_categories) return false;
                        return event.phb_categories.some(cat => cat.category === phbCategory);
                    }});
                }}
                
                // Update the timeline
                updateTimeline(filteredData);
            }}
            
            // Search functionality
            function searchTimeline() {{
                const searchTerm = document.getElementById('search-input').value.toLowerCase();
                
                if (searchTerm === '') {{
                    // Reset to current filters if search is cleared
                    const specialty = document.getElementById('specialty-filter').value;
                    const year = document.getElementById('year-filter').value;
                    const phbCategory = document.getElementById('phb-filter').value;
                    applyFilters(specialty, year, phbCategory);
                    return;
                }}
                
                // Search in title, events, content, and PHB categories
                const filteredData = eventData.filter(event => {{
                    // Search in title and content
                    if (event.title.toLowerCase().includes(searchTerm) || 
                        (event.content && event.content.toLowerCase().includes(searchTerm))) {{
                        return true;
                    }}
                    
                    // Search in events
                    if (event.events && event.events.some(e => e.toLowerCase().includes(searchTerm))) {{
                        return true;
                    }}
                    
                    // Search in PHB categories
                    if (event.phb_categories && event.phb_categories.some(cat => 
                        cat.category.toLowerCase().includes(searchTerm) || 
                        cat.description.toLowerCase().includes(searchTerm))) {{
                        return true;
                    }}
                    
                    // Search in PHB supports
                    if (event.phb_supports && event.phb_supports.some(sup => 
                        sup.support.toLowerCase().includes(searchTerm) || 
                        sup.description.toLowerCase().includes(searchTerm))) {{
                        return true;
                    }}
                    
                    return false;
                }});
                
                updateTimeline(filteredData);
            }}
            
            // Update the timeline with filtered data
            function updateTimeline(filteredData) {{
                // Create new traces for the filtered data
                const traces = [];
                
                // Get the color map
                const specialties = [...new Set(filteredData.map(item => item.specialty))];
                const colorMap = {{}};
                specialties.forEach(specialty => {{
                    const hash = specialty.split('').reduce((acc, char) => {{
                        return acc + char.charCodeAt(0);
                    }}, 0);
                    colorMap[specialty] = `rgb(${{hash % 256}}, ${{(hash / 256) % 256}}, ${{(hash / 65536) % 256}})`;
                }});
                
                // Create scatter plot traces
                filteredData.forEach((row, i) => {{
                    const date = new Date(row.date);
                    
                    // Prepare hover text
                    let hoverText = `<b>${{row.title}}</b><br>` +
                                   `Date: ${{date.toISOString().split('T')[0]}}<br>` +
                                   `Specialty: ${{row.specialty}}<br>`;
                    
                    if (row.personnel) {{
                        hoverText += `Personnel: ${{row.personnel.join(', ')}}<br>`;
                    }}
                    
                    if (row.events) {{
                        hoverText += `Events: ${{row.events.slice(0, 2).join(', ')}}<br>`;
                    }}
                    
                    if (row.phb_categories && row.phb_categories.length > 0) {{
                        const phbCats = row.phb_categories.map(cat => `${{cat.category}} (${{cat.severity}})`);
                        hoverText += `PHB Categories: ${{phbCats.join(', ')}}<br>`;
                    }}
                    
                    // Determine marker size based on PHB relevance
                    let markerSize = 15;
                    if (row.phb_categories && row.phb_categories.length > 0) {{
                        markerSize = 20;
                    }}
                    
                    traces.push({{
                        x: [date],
                        y: [row.specialty],
                        mode: 'markers',
                        marker: {{
                            size: markerSize,
                            color: colorMap[row.specialty],
                            line: {{width: 2, color: 'DarkSlateGrey'}}
                        }},
                        name: row.title,
                        text: hoverText,
                        hoverinfo: 'text',
                        customdata: [i]
                    }});
                }});
                
                // Create table trace
                const tableTrace = {{
                    type: 'table',
                    header: {{
                        values: ["Date", "Title", "Specialty", "PHB Categories"],
                        fill: {{color: 'rgba(50, 50, 50, 1)'}},
                        align: 'left',
                        font: {{color: 'white', size: 12}}
                    }},
                    cells: {{
                        values: [
                            filteredData.map(item => new Date(item.date).toISOString().split('T')[0]),
                            filteredData.map(item => item.title),
                            filteredData.map(item => item.specialty),
                            filteredData.map(item => {{
                                if (item.phb_categories && item.phb_categories.length > 0) {{
                                    return item.phb_categories.map(cat => `${{cat.category}} (${{cat.severity}})`).join(', ');
                                }}
                                return '';
                            }})
                        ],
                        fill: {{color: 'rgba(30, 30, 30, 0.8)'}},
                        align: 'left',
                        font: {{color: 'white', size: 11}}
                    }}
                }};
                
                // Add the table trace
                traces.push(tableTrace);
                
                // Update the plot with new data
                Plotly.react('timeline', traces, {json.dumps(fig_dict['layout'])});
            }}
            
            // Tab functionality
            function openTab(evt, tabName) {{
                // Hide all tab content
                const tabContents = document.getElementsByClassName('tab-content');
                for (let i = 0; i < tabContents.length; i++) {{
                    tabContents[i].classList.remove('active');
                }}
                
                // Remove active class from all tabs
                const tabs = document.getElementsByClassName('tab');
                for (let i = 0; i < tabs.length; i++) {{
                    tabs[i].classList.remove('active');
                }}
                
                // Show the selected tab content and mark the button as active
                document.getElementById(tabName).classList.add('active');
                evt.currentTarget.classList.add('active');
            }}
        </script>
    </body>
    </html>
    """
    
    # Write the HTML file
    with open('gwendolyn_medical_timeline_phb.html', 'w') as f:
        f.write(html_content)
    
    print("PHB-integrated timeline saved to gwendolyn_medical_timeline_phb.html")

def main():
    # Check if data file exists
    if not os.path.exists('gwendolyn_medical_data.json') and not os.path.exists('gwendolyn_medical_data_enhanced.json'):
        print("Error: No medical data JSON file found. Run parse_enex.py or enhanced_parse_enex.py first.")
        return
    
    # Load data
    data = load_data()
    
    # Create PHB-integrated timeline
    create_phb_timeline(data)

if __name__ == "__main__":
    main()
