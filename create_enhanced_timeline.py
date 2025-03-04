import json
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def load_data():
    """Load the medical data from JSON file"""
    with open('gwendolyn_medical_data.json', 'r') as f:
        data = json.load(f)
    
    # Convert date strings to datetime objects
    for item in data:
        if item['date']:
            item['date'] = datetime.strptime(item['date'], '%Y-%m-%d')
    
    return data

def create_enhanced_timeline(data):
    """Create an enhanced interactive timeline visualization"""
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
        subplot_titles=("Medical Timeline", "Event Details")
    )
    
    # Add events to the timeline
    for i, row in df.iterrows():
        hover_text = f"<b>{row['title']}</b><br>"
        hover_text += f"Date: {row['date'].strftime('%Y-%m-%d')}<br>"
        hover_text += f"Specialty: {row['specialty']}<br>"
        hover_text += f"Personnel: {', '.join(row['personnel'])}<br>"
        hover_text += f"Events: {', '.join(row['events'][:2])}<br>"
        
        fig.add_trace(
            go.Scatter(
                x=[row['date']],
                y=[row['specialty']],
                mode='markers',
                marker=dict(
                    size=15,
                    color=color_map[row['specialty']],
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
    fig.add_trace(
        go.Table(
            header=dict(
                values=["Date", "Title", "Specialty", "Personnel", "Events"],
                fill_color='rgba(50, 50, 50, 1)',
                align='left',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=[
                    df['date'].dt.strftime('%Y-%m-%d'),
                    df['title'],
                    df['specialty'],
                    [', '.join(p) for p in df['personnel']],
                    [', '.join(e[:2]) for e in df['events']]
                ],
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
            'text': "Gwendolyn Vials Moore - Medical History Timeline",
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
        showlegend=False,
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.1,
                y=1.1,
                buttons=[
                    dict(
                        label="All Specialties",
                        method="update",
                        args=[{"visible": [True] * len(df) + [True]}]
                    )
                ] + [
                    dict(
                        label=specialty,
                        method="update",
                        args=[{"visible": [row['specialty'] == specialty for _, row in df.iterrows()] + [True]}]
                    ) for specialty in sorted(specialties) if specialty != "Unknown"
                ]
            )
        ]
    )
    
    # Add annotations for significant events
    significant_years = df.groupby(df['date'].dt.year).size().sort_values(ascending=False).head(3).index.tolist()
    
    for year in significant_years:
        year_data = df[df['date'].dt.year == year]
        if not year_data.empty:
            max_events = year_data.iloc[0]
            fig.add_annotation(
                x=max_events['date'],
                y=max_events['specialty'],
                text=f"Significant activity in {year}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="white",
                ax=0,
                ay=-40
            )
    
    # Add instructions
    fig.add_annotation(
        x=0.5,
        y=1.05,
        xref="paper",
        yref="paper",
        text="Use the buttons above to filter by specialty. Hover over points for details. Use the slider below to zoom in on time periods.",
        showarrow=False,
        font=dict(size=12, color="white"),
        align="center",
        bgcolor="rgba(50, 50, 50, 0.8)",
        bordercolor="white",
        borderwidth=1,
        borderpad=4
    )
    
    # Save the figure as JSON for the HTML template
    fig_json = fig.to_json()
    fig_dict = json.loads(fig_json)
    
    # Convert data to JSON for JavaScript
    data_json = []
    for item in data:
        data_json.append({
            'title': item['title'],
            'date': item['date'].strftime('%Y-%m-%d') if item['date'] else None,
            'specialty': item['specialty'],
            'personnel': item['personnel'],
            'events': item['events'],
            'content': item['content']
        })
    
    # Create the HTML content with the JSON data embedded
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gwendolyn Vials Moore - Medical History Timeline</title>
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
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Gwendolyn Vials Moore - Medical History Timeline</h1>
            
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
            </div>
            
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Search for keywords in events or titles..." onkeyup="searchTimeline()">
            </div>
            
            <div id="timeline" class="timeline"></div>
            
            <div class="info-panel">
                <h2>Selected Event Details</h2>
                <div id="event-details">Click on a point in the timeline to see details</div>
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
                        <p><strong>Personnel:</strong> ${{event.personnel.join(', ')}}</p>
                        <p><strong>Events:</strong></p>
                        <ul>
                            ${{event.events.map(e => `<li>${{e}}</li>`).join('')}}
                        </ul>
                        <p><strong>Content:</strong> ${{event.content}}</p>
                    `;
                    
                    document.getElementById('event-details').innerHTML = detailsHtml;
                }}
            }});
            
            // Filter by specialty
            function filterBySpecialty() {{
                const specialty = document.getElementById('specialty-filter').value;
                const yearFilter = document.getElementById('year-filter').value;
                
                applyFilters(specialty, yearFilter);
            }}
            
            // Filter by year
            function filterByYear() {{
                const specialty = document.getElementById('specialty-filter').value;
                const year = document.getElementById('year-filter').value;
                
                applyFilters(specialty, year);
            }}
            
            // Apply both filters
            function applyFilters(specialty, year) {{
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
                    applyFilters(specialty, year);
                    return;
                }}
                
                // Search in title, events, and content
                const filteredData = eventData.filter(event => {{
                    return event.title.toLowerCase().includes(searchTerm) || 
                           event.events.some(e => e.toLowerCase().includes(searchTerm)) ||
                           (event.content && event.content.toLowerCase().includes(searchTerm));
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
                    
                    const hoverText = `<b>${{row.title}}</b><br>` +
                                     `Date: ${{date.toISOString().split('T')[0]}}<br>` +
                                     `Specialty: ${{row.specialty}}<br>` +
                                     `Personnel: ${{row.personnel.join(', ')}}<br>` +
                                     `Events: ${{row.events.slice(0, 2).join(', ')}}<br>`;
                    
                    traces.push({{
                        x: [date],
                        y: [row.specialty],
                        mode: 'markers',
                        marker: {{
                            size: 15,
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
                        values: ["Date", "Title", "Specialty", "Personnel", "Events"],
                        fill: {{color: 'rgba(50, 50, 50, 1)'}},
                        align: 'left',
                        font: {{color: 'white', size: 12}}
                    }},
                    cells: {{
                        values: [
                            filteredData.map(item => new Date(item.date).toISOString().split('T')[0]),
                            filteredData.map(item => item.title),
                            filteredData.map(item => item.specialty),
                            filteredData.map(item => item.personnel.join(', ')),
                            filteredData.map(item => item.events.slice(0, 2).join(', '))
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
        </script>
    </body>
    </html>
    """
    
    # Write the HTML file
    with open('gwendolyn_medical_timeline_enhanced.html', 'w') as f:
        f.write(html_content)
    
    print("Enhanced timeline saved to gwendolyn_medical_timeline_enhanced.html")

def main():
    # Check if data file exists
    if not os.path.exists('gwendolyn_medical_data.json'):
        print("Error: gwendolyn_medical_data.json not found. Run parse_enex.py first.")
        return
    
    # Load data
    data = load_data()
    
    # Create enhanced timeline
    create_enhanced_timeline(data)

if __name__ == "__main__":
    main()
