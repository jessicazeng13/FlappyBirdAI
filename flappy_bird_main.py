import pygame
import neat
import time
import os
import random
pygame.font.init() 

WIN_WIDTH = 500 # constant values
WIN_HEIGHT = 800 

## LOAD IMAGES & FONTS ##
# store all 3 images of bird in a list, note store 2x means double the size
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))), 
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))), 
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))
STAT_FONT = pygame.font.SysFont("comicsans", 50) #font for the score

##### BIRD CLASS
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25   #bird tilt
    ROT_VEL = 20        #how much we rotate on each frame
    ANIMATION_TIME = 5  #how long each bird animation is shown

    def __init__(self, x, y):
        self.x = x      #starting positions
        self.y = y
        self.tilt = 0   #tilt of the image
        self.tick_count = 0 #physics 
        self.vel = 0
        self.height = self.y
        self.img_count = 0   #control image we are showing, for animation
        self.img = self.IMGS[0]   #which image we are showing, for animation

    # Jump function 
    def jump(self):
        self.vel = -10.5   #negative velocity means up	
        self.tick_count = 0   #keep track of when we last jumped
        self.height = self.y  #where the bird jumped from, or original position

    # Move function, we call this every frame where we move our bird
    def move(self):
        self.tick_count += 1 #keep track of ticks/frames since last jump

        # Displacement, how many pixels we move up or down (y) this frame
        # Formula for displacement
        displacement = self.vel*self.tick_count + 1.5*self.tick_count**2 

        # Terminal velocity:
        if displacement >= 16: #if we are moving down more than 16 pixels
            displacement = 16

        if displacement < 0: #if we are moving up
            displacement -= 2 # IF we are moving upwards, move up a little more

        self.y = self.y + displacement #update y position

        # Tilt the bird
        if displacement < 0 or self.y < self.height + 50: #if we are moving upwards or we are above the jump height
            if self.tilt < self.MAX_ROTATION: 
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL #rotate downwards, like a nosedive


    # Draw function
    def draw(self, win): # win = window we are drawing on
        self.img_count += 1 #keep track of how many times we have shown ONE image

        # Determine which image we use based on image count
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0  #reset the image count
        
        # If the bird is nosediving, we don't want to flap
        if self.tilt <= -80:
            self.img = self.IMGS[1] #level wing image
            self.img_count = self.ANIMATION_TIME*2 # so if we jump back up, animation starts again

        # Rotate the image around its centre (pygame)
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect
                                          (topleft = (self.x, self.y)).center) #got this from tutorial
        #define the rectangle around the image, and rotate around the centre of the image (x, y)

        # Draw (blit) the image on the screen/window
        win.blit(rotated_image, new_rect.topleft)

    # Get the mask for the current image of the bird (for collision)
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


##### PIPE CLASS
class Pipe:
    GAP = 200 #gap between the pipes
    VEL = 5 #how fast the pipes move towards the bird
    
    def __init__(self, x):
        self.x = x
        self.height = 0

        self.top = 0        # where the top of the pipe is
        self.bottom = 0     # where the bottom of the pipe is
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False #if the bird has passed the pipe (for collision)
        self.set_height() # call a method to set the height of the pipe

    def set_height(self):
        self.height = random.randrange(50, 450) #random height between 50 and 450
        self.top = self.height - self.PIPE_TOP.get_height() 
        self.bottom = self.height + self.GAP

    # Move the pipe towards the bird (change x position)
    def move(self):
        self.x -= self.VEL

    # Draw the pipe on the window (draws top and bottom),
    # x changes, y doesnt
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # PIXEL collision detection
    def collide(self, bird):
        # Get the masks of the bird and the pipes (lists i believe)
        bird_mask = bird.get_mask() 
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Offset is the distance between the bird and the pipe (took thi from tut, dont really get it)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Find points of collision - using pygame
        # b_point is point of overlap between bird_mask & bottom_mask, using the bottom_offset
        b_point = bird_mask.overlap(bottom_mask, bottom_offset) #returns None if no collision
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point: #if there is a collision (if not none)
            return True #there is collision
        return False
    

# BASE CLASS
class Base:
    VEL = 5 #velocity of the base, has to be same as pipe velocity
    WIDTH = BASE_IMG.get_width() 
    IMG = BASE_IMG

    # Initialise 2 of the same images side by side
    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    # Move the base towards the bird
    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # If the first image is off the screen, move it to the end of the second image
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        # Same for the second image
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    # Draw the base on the window
    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))




def draw_window(win, bird, pipes, base, score):
    # Draw the background image
    win.blit(BG_IMG, (0,0))

    # Draw the pipes
    for pipe in pipes:
        pipe.draw(win)

    # Render the score (text + string, ?, colour)
    text = STAT_FONT.render("Score: " + str(score), 1, (255,255,255)) 
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10)) #position of the score

    # Draw the base & bird
    base.draw(win)
    bird.draw(win) 

    # Update the display
    pygame.display.update() 


## MAIN FUNCTION ## gemones & config for NEAT fitness functions
def main(genomes, config):
    bird = Bird(230, 250)
    base = Base(730) #bottom of the screen
    pipes = [Pipe(700)] #initialise pipe x position at 700?
    run = True
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT)) #create window
    score = 0

    # Create clock object from pygame
    clock = pygame.time.Clock()

    # Game loop
    while run:
        clock.tick(30) #at most, 30 ticks per second
        for event in pygame.event.get():  #check for events i.e click
            if event.type == pygame.QUIT: #if we click the X window button
                run = False

        # bird.move() # move the bird for every tick
        base.move()

        add_pipe = False
        remove = [] #list to store pipes we want to remove
        for pipe in pipes:         
            # Check for collision
            if pipe.collide(bird):
                pass

            # Once x position of a pipe is completely off the screen, add a new pipe
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                remove.append(pipe)

            # Checks if bird has passed the pipe
            if not pipe.passed and pipe.x < bird.x:  # Do not understand this one
                pipe.passed = True
                add_pipe = True

            pipe.move()

        if add_pipe:
            score += 1
            pipes.append(Pipe(700)) #create new pipe, if you want pipes closer together, can make like 650
        
        # remove pipes from the list
        for r in remove:
            pipes.remove(r)

        # Check if bird hits the ground	
        if bird.y + bird.img.get_height() >= 730:
            pass

        draw_window(win, bird, pipes, base, score)

    pygame.quit()
    quit()
 
main()


# Function to run
def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    
    # Create the population, passing in the config file
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Set the fitness function as main
    winner = p.run(main, 50) #run the main function 50 generations

# Configuration file
if __name__ == "__main__":
    # Get theabs path to the directiory we are in
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)