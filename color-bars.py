##
#
# Color Bars
# Copyright (C) (2019) Beny Synakiewicz
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##

##
#
# Imports.
#
##

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from itertools import chain
from pathlib import Path
from string import Template
from sys import exit
from timeit import default_timer as timer
from types import SimpleNamespace
from typing import List, Optional

from cv2 import blur, imwrite, resize, VideoCapture, CAP_PROP_FRAME_COUNT, IMWRITE_PNG_COMPRESSION, INTER_LANCZOS4
from numpy import concatenate, ndarray

##
#
# Globals.
#
##

# The application.

Application = SimpleNamespace(
	Name = "Color Bars",
	Version = "1.1",
	Creator = "Beny Synakiewicz",
	URL = "www.beny-synakiewicz.com",
)

# The user interface.

UpdateInterval = 1.0
Separator = "  |  "
Indent = 4 * " "

# The output file.

OutputSuffix = "png"
OutputOptions = [IMWRITE_PNG_COMPRESSION, 9]

OutputPostfix = SimpleNamespace(
	Columns = "(Columns)",
	ColumnsBlurred = "(Blurred Columns)",
	SolidColor = "(Solid Color)",
)

# The image processing.

Defaults = SimpleNamespace(
	X = 1920,
	Y = 1080,
)

InterpolationMethod = INTER_LANCZOS4
BlurHeight = 300

##
#
# The main function.
#
##

def Main() -> None:

	##
	#
	# Welcome the user.
	#
	##

	print(f"{Application.Name} {Application.Version}, by {Application.Creator} ({Application.URL})")

	##
	#
	# Process the command-line arguments.
	#
	##

	print()

	# Initialize and launch the argument parser.

	parser = ArgumentParser(
		description = "Creates a movie barcode of a given video file.",
		formatter_class = ArgumentDefaultsHelpFormatter
	)

	parser.add_argument("-x", dest = "X", type = int, default = Defaults.X, help = "output image width")
	parser.add_argument("-y", dest = "Y", type = int, default = Defaults.Y, help = "output image height")
	parser.add_argument("-o", dest = "Output", type = Path, default = Path(), help = "output directory path")
	parser.add_argument("Input", type = Path, nargs = "+", help = "input file path")

	arguments = parser.parse_args()

	# Print some (mildly) helpful information.

	print('(The time format used in the progress indication is "HH:MM:SS".)' + "\n")

	# Verify the output image parameters.

	if arguments.X < 1 or arguments.Y < 1:
		Error(f"Invalid given output image dimensions: {arguments.X}x{arguments.Y}.", critical = True)

	# Create a list of input files.

	inputFilePaths = map(lambda path: [path] if ".txt" != path.suffix.lower() else ReadListOfPaths(path), arguments.Input)
	inputFilePaths = list(set(chain.from_iterable(inputFilePaths)))

	if not inputFilePaths:
		Error("No input files were given.", critical = True)

	print(f"Found {len(inputFilePaths)} input video file(s)." "\n")

	# Check and, if necessary, create the output directory.

	if not arguments.Output.is_dir():

		if arguments.Output.exists():

			Error("The given output directory ALREADY EXISTS and IS NOT A DIRECTORY.", critical = True)

		else:

			arguments.Output.mkdir(parents = True)

			if not arguments.Output.is_dir():
				Error("The given output directory DOES NOT EXIST and CANNOT BE CREATED.", critical = True)

	# Process the input files.

	for path in inputFilePaths:

		# Print some information on the file.

		print("\n" f"Current file: {path}." "\n")

		# Verify the input file.

		if not path.is_file():
			Error("The given input file DOES NOT EXIST.", indent = Indent)
			continue

		# Generate and verify the output file paths.

		outputPathTemplate = arguments.Output / f"{path.stem} $postfix.{OutputSuffix}"

		outputPaths = SimpleNamespace(**{
			key: SubstituteInPath(outputPathTemplate, "postfix", postfix)
			for (key, postfix) in NamespaceItems(OutputPostfix)
		})

		if any(path.exists() for _, path in NamespaceItems(outputPaths)):
			Error("Some (or all) of the output files ALREADY EXIST.", indent = Indent)
			continue

		##
		#
		# Open the input video file.
		#
		##

		stream = VideoCapture(str(path))

		if not stream.isOpened():
			Error("Failed to open the given input file.", indent = Indent)
			continue

		##
		#
		# Process the video.
		#
		##

		frameCount = int(stream.get(CAP_PROP_FRAME_COUNT))
		frames = SimpleNamespace(
			Current = 0,
			Count = frameCount,
			N = frameCount // arguments.X
		)

		time = SimpleNamespace(
			Start = timer(),
			Latest = 0,
			Information = 0,
		)

		columns = []

		while stream.isOpened():

			time.Latest = timer()

			# Attempt to grab the next frame (and decide whether to skip it).

			if not stream.grab():
				break

			frames.Current += 1

			if frames.N and (frames.Current % frames.N):
				continue

			# Retrieve the frame.

			_, frame = stream.retrieve()

			# Display information regarding the progress.

			if (time.Latest - time.Information > UpdateInterval):

				progress = frames.Current / frames.Count
				timePassed = time.Latest - time.Start
				timeLeft = (timePassed / progress) - timePassed

				print(
					Indent
					+ f"{progress:6.1%}"
					+ Separator + HumanizeTime(timePassed) + " passed"
					+ Separator + HumanizeTime(timeLeft) + " left"
				)

				time.Information = time.Latest

			# Process the retrieved frame.

			columns.append(Interpolate(frame, width = 1))

		# Display the "Finished!" information.

		print("\n" + Indent + f"Finished! Processing the video took {HumanizeTime(time.Latest - time.Start)}.")

		##
		#
		# Generate and save the output images.
		#
		##

		# Generate the output images.

		print("\n" + Indent + "Generating the output images...")

		baseOutputImage = Interpolate(concatenate(columns, axis = 1), arguments.X, arguments.Y)
		outputImages = SimpleNamespace(

			Columns = baseOutputImage,
			ColumnsBlurred = blur(baseOutputImage, (1, BlurHeight)),
			SolidColor = Interpolate(Interpolate(baseOutputImage, height = 1), height = arguments.Y),

		)

		# Save the output images.

		print(Indent + "Saving the generated images...")

		if not SaveImage(outputImages.Columns, outputPaths.Columns):
			Error(f"Failed to save an output image: {outputPaths.Columns}.", indent = Indent)
			continue

		if not SaveImage(outputImages.ColumnsBlurred, outputPaths.ColumnsBlurred):
			Error(f"Failed to save an output image: {outputPaths.ColumnsBlurred}.", indent = Indent)
			continue

		if not SaveImage(outputImages.SolidColor, outputPaths.SolidColor):
			Error(f"Failed to save an output image: {outputPaths.SolidColor}.", indent = Indent)
			continue

##
#
# Utilities.
#
##

def Error(description: str, indent: str = "", critical: bool = False) -> None:

	print(indent + "ERROR: " + description)

	if critical:
		exit(1)

def HumanizeTime(seconds: int) -> str:

	hours, remainder = divmod(seconds, 60 * 60)
	minutes, seconds = divmod(remainder, 60)

	return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"

def Interpolate(image: ndarray, width: Optional[int] = None, height: Optional[int] = None) -> ndarray:

	originalHeight, originalWidth, _ = image.shape

	return resize(
		image,
		(width or originalWidth, height or originalHeight),
		interpolation = InterpolationMethod
	)

def NamespaceItems(namespace: SimpleNamespace):

	return vars(namespace).items()

def ReadListOfPaths(filePath: Path) -> List[Path]:

	return [Path(path) for path in filePath.read_text().splitlines()]

def SaveImage(image: ndarray, path: Path) -> bool:

	return bool(imwrite(str(path), image, OutputOptions))

def SubstituteInPath(path: Path, identifier: str, value: str) -> Path:

	return Path(Template(str(path)).substitute({identifier: value}))

##
#
# The start-up routine.
#
##

try:

	Main()

except KeyboardInterrupt:

	pass