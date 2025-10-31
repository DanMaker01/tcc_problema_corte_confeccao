

class Malha():
    def __init__(self,W,L,R,C):
        self.W =W
        self.L = L
        self.R = R
        self.C = C
        pass
    def gx(self):
        return self.L / (self.C - 1)
    def gy(self):
        return self.W / (self.R - 1)
    def D(self):
        return self.C * self.R

    def n_to_coord(self, n) -> tuple:
        c = n // self.R
        r = n % self.R
        return (c * self.gx(), r * self.gy())
    
    def coord_to_n(self, x, y) -> int:
        c = round(x / self.gx())
        r = round(y / self.gy())
        n = c * self.R + r
        print(f"(x,y): ({x:.2f},{y:.2f}) -> n: {n}\t(c,r)=({c},{r})\tC:{self.C} R:{self.R}")
        return n

    
    def retornar_pontos_malha(self) -> dict:
        pontos = {}
        for i in range(self.C):
            for j in range(self.R):
                n = i*self.R+j
                pontos[n] = (i*self.gx(), j*self.gy())
        return pontos
        

