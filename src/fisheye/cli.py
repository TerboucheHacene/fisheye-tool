import typer

from fisheye.projection import FisheyeToPerspective
from fisheye.schemas import CameraType, FisheyeFormat

app = typer.Typer()


@app.command()
def fisheye_to_perspective(
    input_file: str,
    output_file: str,
    fov: float = 180,
    perspective_fov: float = 120,
    camera_type: CameraType = CameraType.EQUIDISTANT,
    format: FisheyeFormat = FisheyeFormat.CIRCULAR,
):
    fisheye_to_perspective = FisheyeToPerspective(
        input_file,
        fov=fov,
        perspective_fov=perspective_fov,
        camera_type=camera_type,
        format=format,
    )
    fisheye_to_perspective(output_file=output_file)
    typer.echo(f"Saved image {output_file}")


if __name__ == "__main__":
    app()
