import numpy as np

from textattack.search_methods import SearchMethod

class BeamSearch(SearchMethod):
    """ 
    An attack that greedily chooses from a list of possible 
    perturbations.
    
    Args:
        goal_function: A function for determining how well a perturbation is doing at achieving the attack's goal.
        transformation (Transformation): The type of transformation.
        beam_width (int): the number of candidates to retain at each step

    """
    def __init__(self, beam_width=8):
        self.beam_width = beam_width
        
    def __call__(self, initial_result):
        beam = [initial_result.tokenized_text]
        best_result = initial_result
        while not best_result.succeeded:
            potential_next_beam = []
            for text in beam:
                transformations = self.get_transformations(
                        text, original_text=initial_result.tokenized_text)
                for next_text in transformations:
                    potential_next_beam.append(next_text)
            if len(potential_next_beam) == 0:
                # If we did not find any possible perturbations, give up.
                return best_result
            results = self.get_goal_results(potential_next_beam, initial_result.output)
            scores = np.array([r.score for r in results])
            best_result = results[scores.argmax()]

            # Refill the beam. This works by sorting the scores
            # in descending order and filling the beam from there.
            best_indices = -scores.argsort()[:self.beam_width]
            beam = [potential_next_beam[i] for i in best_indices]
        return best_result

    def extra_repr_keys(self):
        return ['beam_width']
