from flask import Blueprint, request, send_file
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend to avoid thread issues with Matplotlib
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import mplcursors  # Import mplcursors for interactive tooltips

# Create a Blueprint for the plot routes
plot_blueprint = Blueprint('plot_routes', __name__)

@plot_blueprint.route('/plot_reviews')
def plot_reviews():
    # Fetch month and count data from request arguments
    months = request.args.getlist('months', type=int)
    counts = request.args.getlist('counts', type=int)

    # Create the figure and axis
    fig, ax = plt.subplots()

    # Create a Line2D plot for reviews per month
    line, = ax.plot(months, counts, color='green', marker='o', linestyle='-', label='Number of Reviews')

    # Set axis properties (Axes Props)
    ax.set_xlim(1, 12)  # Set the x-axis limit from 1 to 12 (months)
    ax.set_ylim(0, max(counts) + 6)  # Adjust the y-axis limit based on data range
    ax.set_title('Monthly Review Counts', fontsize=14, fontweight='bold')  # Title with font size and weight
    ax.set_xlabel('Month', fontsize=12)  # X-axis label with font size
    ax.set_ylabel('Number of Reviews', fontsize=12)  # Y-axis label with font size
    ax.set_xticks(range(1, 13))  # Set x-axis ticks for each month
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], 
                       fontsize=10)  # Set x-axis tick labels with font size

    # Add grid for better readability
    ax.grid(True, linestyle='--', linewidth=0.7, alpha=0.7)  # Grid with dashed lines and some transparency

    # Add a legend
    ax.legend(loc='upper left', fontsize=10)  # Add a legend with custom location and font size

    # Add interactive tooltips
    mplcursors.cursor(line, hover=True).connect("add", lambda sel: sel.annotation.set_text(f"Total: {counts[sel.index]}, {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][sel.index]}"))

    # Save the plot to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Return the plot as an image response
    return send_file(buf, mimetype='image/png')
