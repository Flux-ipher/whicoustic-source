
import numpy as np
from fastapi.encoders import jsonable_encoder
import sys

def test_encoder():
    print(f"Numpy version: {np.__version__}")
    
    data = {"bool_val": np.bool_(True), "start_val": True}
    print(f"Data types: {[type(v) for v in data.values()]}")
    
    try:
        encoded = jsonable_encoder(data)
        print("Standard encoder success:", encoded)
    except Exception as e:
        print("Standard encoder failed:", e)
        
    try:
        encoded = jsonable_encoder(
            data,
            custom_encoder={
                np.bool_: bool,
                np.integer: int,
                np.floating: float,
                np.ndarray: lambda x: x.tolist()
            }
        )
        print("Custom encoder success:", encoded)
    except Exception as e:
        print("Custom encoder failed:", e)

    # Check the type explicitly reported in error
    print(f"np.bool_: {np.bool_}")
    try:
        print(f"np.bool: {np.bool}")
    except AttributeError:
        print("np.bool does not exist")

if __name__ == "__main__":
    test_encoder()
