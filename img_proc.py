import argparse
from datadog import initialize, statsd
import matplotlib.pyplot as plt
from PIL import Image
import time

plot_resolution = (250, 35) # (number of points on a line, number of lines)

def process_image(file_name):
  im = Image.open(file_name)
  px = im.load()

  sample_magnitudes = []

  sample_width = int(im.size[0] / (plot_resolution[0] / 2))
  sample_height = int(im.size[1] / plot_resolution[1])

  # each horizontal slice
  for y_index in reversed(range(int(im.size[1]/sample_height))):
    sample_magnitudes.append([])

    # each vertical slice of that (actual sampled region)
    for x_index in range(int(im.size[0]/sample_width)):
      x, y = x_index * sample_width, y_index * sample_height
      # get the collection of pixels we want to sample
      pixels = [[im.getpixel((x+i, y+j)) for j in range(sample_height) ] for i in range(sample_width)]

      # each pixel is a (r,g,b) tuple and we have a 2d array of them so sum(sum(sum()))
      sample_magnitudes[-1].append(sum([sum([sum(p) for p in l]) for l in pixels]))

  # scale magnitudes
  max_mag = max([max(sample_row) for sample_row in sample_magnitudes])
  min_mag = min([min(sample_row) for sample_row in sample_magnitudes])
  def scale_mag(sample_mag):
    return 1 - (sample_mag - min_mag) / (max_mag - min_mag)

  sample_magnitudes = [[scale_mag(sample) for sample in sample_row] for sample_row in sample_magnitudes]    

  # plot the lines
  xs = [x*sample_width/2 for x in range(2*int(im.size[0]/sample_width))]

  ys = []
  for row_num in range(len(sample_magnitudes)):
    base_row_height = row_num*sample_height
    row_ys = []
    for sample in sample_magnitudes[row_num]:
      y = sample*sample_height/1.8
      row_ys.append(base_row_height + y)
      row_ys.append(base_row_height - y)
    ys.append(row_ys)

  plotting_dict = {'x': xs}
  plotting_dict.update({'y:'+str(i): ys[i] for i in range(len(ys))})
  
  return plotting_dict

def plot_with_mpl(plotting_dict):
  for line in range(len(plotting_dict) - 1):
    plt.plot('x', str('y:'+str(line)), '', data=plotting_dict)

  print(len(plotting_dict['x']))
  plt.show()

def plot_with_dd(plotting_dict):

  # submit points to datadog

  options = {'statsd_host':'127.0.0.1', 'statsd_port':8125}
  initialize(**options)

  for i in range(len(plotting_dict['x'])):
    for key, vals in plotting_dict.items():
      statsd.gauge('example_metric.iain', vals[i], tags=[key])
    time.sleep(10)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description = 'Plot an image as a graph')
  parser.add_argument('file_name', help='filename of image to plot')
  parser.add_argument('--preview', help='should the plot be previewed with matplotlib', action='store_true')
  args = parser.parse_args()
  
  if args.file_name:
    processed_image = process_image(args.file_name)

  if args.preview:
    plot_with_mpl(processed_image)
  else:
    plot_with_dd(processed_image)
  


