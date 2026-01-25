"""
Demostración de cómo funciona la seed con random.Random()
"""

import random


def demo_sin_seed():
    """Sin seed: números diferentes cada vez"""
    print("=" * 50)
    print("SIN SEED (aleatorio puro)")
    print("=" * 50)

    print("\nEjecución 1:")
    rng1 = random.Random()  # Sin seed
    for i in range(5):
        print(f"  Número {i+1}: {rng1.randint(1, 100)}")

    print("\nEjecución 2:")
    rng2 = random.Random()  # Sin seed (otra vez)
    for i in range(5):
        print(f"  Número {i+1}: {rng2.randint(1, 100)}")

    print("\n⚠️  Los números son DIFERENTES")


def demo_con_seed():
    """Con seed: números idénticos cada vez"""
    print("\n" + "=" * 50)
    print("CON SEED = 42 (determinista)")
    print("=" * 50)

    print("\nEjecución 1 (seed=42):")
    rng1 = random.Random(42)  # Con seed 42
    numeros1 = []
    for i in range(5):
        num = rng1.randint(1, 100)
        numeros1.append(num)
        print(f"  Número {i+1}: {num}")

    print("\nEjecución 2 (seed=42):")
    rng2 = random.Random(42)  # Con seed 42 (otra vez)
    numeros2 = []
    for i in range(5):
        num = rng2.randint(1, 100)
        numeros2.append(num)
        print(f"  Número {i+1}: {num}")

    print(f"\n✅ Los números son IDÉNTICOS: {numeros1 == numeros2}")


def demo_seeds_diferentes():
    """Seeds diferentes: resultados diferentes"""
    print("\n" + "=" * 50)
    print("SEEDS DIFERENTES")
    print("=" * 50)

    print("\nSeed = 42:")
    rng1 = random.Random(42)
    for i in range(5):
        print(f"  Número {i+1}: {rng1.randint(1, 100)}")

    print("\nSeed = 99:")
    rng2 = random.Random(99)
    for i in range(5):
        print(f"  Número {i+1}: {rng2.randint(1, 100)}")

    print("\n⚠️  Seeds diferentes → resultados diferentes")


def demo_choice_con_lista():
    """Simula cómo funciona en tu proyecto"""
    print("\n" + "=" * 50)
    print("SIMULACIÓN DE TU PROYECTO")
    print("=" * 50)

    layouts = [
        "Central Ruin",
        "Open Edges",
        "Forest",
        "Mountain Pass",
        "River Crossing",
    ]
    deployments = ["Opposite Edges", "Corners", "Diagonal", "Center vs Edge"]
    objectives = ["Hold Center", "Secure Supplies", "Domination", "King of the Hill"]

    print("\nGeneración 1 (seed=42):")
    rng1 = random.Random(42)
    print(f"  Layout:     {rng1.choice(layouts)}")
    print(f"  Deployment: {rng1.choice(deployments)}")
    print(f"  Objective:  {rng1.choice(objectives)}")

    print("\nGeneración 2 (seed=42):")
    rng2 = random.Random(42)
    print(f"  Layout:     {rng2.choice(layouts)}")
    print(f"  Deployment: {rng2.choice(deployments)}")
    print(f"  Objective:  {rng2.choice(objectives)}")

    print("\n✅ EXACTAMENTE lo mismo!")

    print("\nGeneración 3 (seed=99):")
    rng3 = random.Random(99)
    print(f"  Layout:     {rng3.choice(layouts)}")
    print(f"  Deployment: {rng3.choice(deployments)}")
    print(f"  Objective:  {rng3.choice(objectives)}")

    print("\n⚠️  Seed diferente → carta diferente")


def demo_formula_simplificada():
    """Ejemplo SIMPLIFICADO de cómo funciona internamente (no es el real)"""
    print("\n" + "=" * 50)
    print("EJEMPLO SIMPLIFICADO DE LA FÓRMULA")
    print("=" * 50)
    print("\nEsto NO es el algoritmo real (es mucho más complejo),")
    print("pero muestra el concepto de determinismo:")
    print()

    def simple_rng(seed, count):
        """Generador pseudo-aleatorio SUPER simplificado"""
        state = seed
        results = []
        for _ in range(count):
            # Fórmula simple (Linear Congruential Generator)
            state = (state * 1103515245 + 12345) & 0x7FFFFFFF
            results.append(state % 100 + 1)
        return results

    print("Seed = 42:")
    nums1 = simple_rng(42, 5)
    print(f"  Números generados: {nums1}")

    print("\nSeed = 42 (otra vez):")
    nums2 = simple_rng(42, 5)
    print(f"  Números generados: {nums2}")

    print(f"\n✅ Iguales: {nums1 == nums2}")

    print("\nSeed = 99:")
    nums3 = simple_rng(99, 5)
    print(f"  Números generados: {nums3}")

    print(f"\n⚠️  Diferentes: {nums1 != nums3}")


if __name__ == "__main__":
    print("\n🎲 DEMOSTRACIÓN: CÓMO FUNCIONA LA SEED EN PYTHON\n")

    demo_sin_seed()
    demo_con_seed()
    demo_seeds_diferentes()
    demo_choice_con_lista()
    demo_formula_simplificada()

    print("\n" + "=" * 50)
    print("CONCLUSIÓN")
    print("=" * 50)
    print("✅ Misma seed → Mismos números (determinista)")
    print("⚠️  Sin seed o seed diferente → Números diferentes")
    print("🔐 La fórmula está en Python (Mersenne Twister)")
    print()
